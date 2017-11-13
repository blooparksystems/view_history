# -*- coding: utf-8 -*-
from openerp import _, api, fields, models, exceptions


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    enable_history = fields.Boolean(
        'Enable History'
    )
    versions = fields.One2many(
        'ir.ui.view.version',
        'view',
        'Versions'
    )
    # current_version is the version of the view that will be rendered
    # do not confuse with the latest version
    current_version = fields.Many2one(
        'ir.ui.view.version',
        'Versions',
        copy=False
    )

    @api.constrains('enable_history')
    def _enable_history_check(self):
        """
        Only allow to enable history for views without inherited views
        TODO: Handle the case of inherited views
        :return:
        """
        if self.enable_history:
            inherited_views = self.search([
                ('inherit_id', '=', self.id)
            ])
            if inherited_views:
                raise exceptions.ValidationError(_(
                    "You can not enable history for (ir.ui.views) records "
                    "with inherited views created."
                ))

    @api.multi
    def write(self, values):
        """
        Redefining the write method to create a new version when changes
        are made in the arch
        :param values:
        :return:
        """
        res = super(IrUiView, self).write(values)
        if not self.env.context.get('avoid_version'):
            if 'enable_history' in values or 'arch' in values:
                for record in self:
                    if record.enable_history:
                        arch = values.get('arch', record.arch)
                        version = self.env['ir.ui.view.version'].create({
                            'view': record.id,
                            'arch': arch
                        })
                        if len(record.versions) == 1:
                            version.set_current()
        return res

    @api.model
    def create(self, vals):
        res = super(IrUiView, self).create(vals)
        if vals.get('enable_history'):
            version = self.env['ir.ui.view.version'].create({
                'view': res.id,
                'arch': res['arch'],
            })
            version.set_current()
        return res

    @api.cr_uid_ids_context
    def render(self, cr, uid, id_or_xml_id, values=None, engine='ir.qweb',
               context=None):
        """
        Set context variable to render current version, not the latest one
        which is the default behaviour
        :param cr:
        :param uid:
        :param id_or_xml_id:
        :param values:
        :param engine:
        :param context:
        :return:
        """
        context = context or {}
        if 'render_version' not in context:
            context['render_version'] = True

        return super(IrUiView, self).render(cr, uid, id_or_xml_id,
                                            values=values, engine=engine,
                                            context=context)

    @api.cr_uid_ids_context
    def read(self, cr, uid, ids, fields=None, context={},
             load='_classic_read'):
        """
        Reading a view:
        - if the variable render_version in context is an integer, then get the
        arch of the specified version
        - if the variable render_version in context is True, then get the
        arch of the current version
        - else get the normal arch
        :param cr:
        :param uid:
        :param ids:
        :param fields:
        :param context:
        :param load:
        :return:
        """
        result = super(IrUiView, self).read(
            cr, uid, ids, fields=fields, context=context, load=load
        )
        if fields and 'arch' in fields and 'render_version' in context:
            render_version = context['render_version']
            for res in result:
                view = self.browse(cr, uid, res['id'])
                if view.enable_history and view.versions:
                    if isinstance(render_version, bool):
                        if render_version:
                            res['arch'] = view.current_version.arch
                    elif isinstance(render_version, int):
                        version = view.versions.filtered(
                            lambda rec: rec.id == render_version
                        )
                        if version:
                            res['arch'] = version.arch
        return result


class IrUiViewVersion(models.Model):
    _name = 'ir.ui.view.version'

    name = fields.Char('Name')
    view = fields.Many2one('ir.ui.view', 'View', required=True)
    arch = fields.Text('Arch')

    # sequence is an incremental sequence value to use it for
    # version names: v1, v2, ...
    sequence = fields.Integer('Sequence')

    # if current is True, it means that is used as current_version
    # of a view
    current = fields.Boolean('Current', compute='_is_current')

    _order = 'id desc'

    def _is_current(self):
        for rec in self:
            rec.current = rec.view.current_version.id == rec.id

    def create(self, vals):
        view = self.env['ir.ui.view'].browse(vals['view'])
        if 'sequence' not in vals:
            sequence = 0
            if view.versions:
                sequence = view.versions[0].sequence + 1
            vals['sequence'] = sequence
        if 'name' not in vals:
            vals['name'] = '%s v%s' % (view.name, vals['sequence'])
        return super(IrUiViewVersion, self).create(vals)

    @api.multi
    def set_current(self):
        """
        Set a version as current.
        - If the version is the latest one, just set as current.
        - Otherwise, create a new version and set it as current.
        :return:
        """
        self.ensure_one()
        view_values = {}
        last_version = self.view.versions[0]
        if self.id == last_version.id:
            view_values.update({
                'current_version': last_version.id
            })
        else:
            current_version = self.create({
                'view': self.view.id,
                'arch': self.arch,
            })
            view_values.update({
                'arch': self.arch,
                'current_version': current_version.id
            })

        # avoid_version is set because we don't want to trigger the creation
        # of a new version when updating the view
        self.with_context(avoid_version=True).view.write(view_values)
