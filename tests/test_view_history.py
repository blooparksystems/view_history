# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, an open source suite of business apps
# This module copyright (C) 2015 bloopark systems (<http://bloopark.de>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tests import common


TEST_ARCH = """<?xml version="1.0"?>
<tree string="List">
    <div> Content </div>
</tree>
"""


class TestViewHistory(common.TransactionCase):
    at_install = False
    post_install = True

    def setUp(self):
        super(TestViewHistory, self).setUp()
        self.test_view = self.env['ir.ui.view'].create({
            'name': 'test view',
            'arch': TEST_ARCH,
            'type': 'qweb',
        })

        self.arch1 = TEST_ARCH.replace('Content', 'Content 1')
        self.arch2 = TEST_ARCH.replace('Content', 'Content 2')
        self.arch3 = TEST_ARCH.replace('Content', 'Content 3')

    def test_00_new_version_after_write(self):
        """ --- Test that a new version is created after write. """

        self.test_view.write({
            'arch': self.arch1
        })
        # No versions are created when enable_history is False
        self.assertEqual(len(self.test_view.versions), 0)

        self.test_view.write({
            'arch': self.arch2,
            'enable_history': True
        })

        # one version is created when activating enable_history
        self.assertEqual(len(self.test_view.versions), 1)

        # version sequence is 0
        # and its content is the changed one
        # is the current one
        version = self.test_view.versions[0]
        self.assertEqual(version.sequence, 0)
        self.assertEqual(version.arch, self.arch2)
        self.assertTrue(version.current)

    def test_01_current_functionality(self):
        """ --- Test set current functionality, set latest as current"""

        self.assertEqual(len(self.test_view.versions), 0)

        self.test_view.write({
            'arch': self.arch1,
            'enable_history': True
        })

        self.assertEqual(len(self.test_view.versions), 1)

        self.test_view.write({
            'arch': self.arch2,
        })

        self.assertEqual(len(self.test_view.versions), 2)

        oldest = self.test_view.versions[1]
        self.assertEqual(oldest.sequence, 0)
        self.assertTrue(
            'v0' in oldest.name
        )
        self.assertEqual(oldest.arch, self.arch1)
        self.assertTrue(oldest.current)

        latest = self.test_view.versions[0]
        self.assertEqual(latest.sequence, 1)
        self.assertTrue(
            'v1' in latest.name
        )
        self.assertEqual(latest.arch, self.arch2)
        self.assertTrue(not latest.current)

        self.assertEqual(
            self.test_view.current_version.id,
            oldest.id
        )
        latest.set_current()
        self.assertEqual(
            self.test_view.current_version.id,
            latest.id
        )

    def test_02_current_functionality(self):
        """ --- Test set current functionality, not latest as current"""

        self.assertEqual(len(self.test_view.versions), 0)

        self.test_view.write({
            'arch': self.arch1,
            'enable_history': True
        })

        self.test_view.write({
            'arch': self.arch2,
        })

        self.test_view.write({
            'arch': self.arch3,
        })

        self.assertEqual(len(self.test_view.versions), 3)

        middle = self.test_view.versions[1]
        middle.set_current()

        # A new version is created
        self.assertEqual(len(self.test_view.versions), 4)

        latest = self.test_view.versions[0]
        self.assertEqual(
            self.test_view.current_version.id,
            latest.id
        )
        self.assertEqual(latest.arch, self.arch2)

    def test_03_read_current_version(self):
        """ Testing the read method with the version option"""

        self.test_view.write({
            'arch': self.arch1,
            'enable_history': True
        })

        self.test_view.write({
            'arch': self.arch2,
        })

        self.test_view.write({
            'arch': self.arch3,
        })

        latest = self.test_view.versions[0]
        middle = self.test_view.versions[1]
        active = self.test_view.versions[2]

        # A normal read returns the latest version of the arch
        res = self.registry.get('ir.ui.view').read(
            self.env.cr, self.env.uid, [self.test_view.id],
            ['arch'])[0]

        self.assertEqual(
            res['arch'], latest.arch
        )

        # When called with render_version=True,
        # read returns the arch the active version of
        res = self.registry.get('ir.ui.view').read(
            self.env.cr, self.env.uid, [self.test_view.id],
            ['arch'], context={'render_version': True})[0]

        self.assertEqual(
            res['arch'], active.arch
        )

        # When called with render_version=specific version id,
        # read returns the arc of the specific version
        res = self.registry.get('ir.ui.view').read(
            self.env.cr, self.env.uid, [self.test_view.id],
            ['arch'], context={'render_version': middle.id})[0]

        self.assertEqual(
            res['arch'], middle.arch
        )
