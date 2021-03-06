# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import unicode_literals

import os

try:
    import webassets
except ImportError:
    webassets = None  # NOQA

from nikola.plugin_categories import LateTask
from nikola import utils


class BuildBundles(LateTask):
    """Bundle assets using WebAssets."""

    name = "build_bundles"

    def set_site(self, site):
        super(BuildBundles, self).set_site(site)
        if webassets is None:
            self.site.config['USE_BUNDLES'] = False

    def gen_tasks(self):
        """Bundle assets using WebAssets."""

        kw = {
            'filters': self.site.config['FILTERS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'theme_bundles': get_theme_bundles(self.site.THEMES),
            'themes': self.site.THEMES,
            'files_folders': self.site.config['FILES_FOLDERS'],
            'code_color_scheme': self.site.config['CODE_COLOR_SCHEME'],
        }

        def build_bundle(output, inputs):
            out_dir = os.path.join(kw['output_folder'],
                                   os.path.dirname(output))
            inputs = [i for i in inputs if os.path.isfile(
                os.path.join(out_dir, i))]
            cache_dir = os.path.join(kw['cache_folder'], 'webassets')
            utils.makedirs(cache_dir)
            env = webassets.Environment(out_dir, os.path.dirname(output),
                                        cache=cache_dir)
            if inputs:
                bundle = webassets.Bundle(*inputs, output=os.path.basename(output))
                env.register(output, bundle)
                # This generates the file
                env[output].urls()
            else:
                with open(os.path.join(out_dir, os.path.basename(output)), 'wb+'):
                    pass  # Create empty file

        yield self.group_task()
        if (webassets is not None and self.site.config['USE_BUNDLES'] is not
                False):
            for name, files in kw['theme_bundles'].items():
                output_path = os.path.join(kw['output_folder'], name)
                dname = os.path.dirname(name)
                file_dep = [os.path.join(kw['output_folder'], dname, fname)
                            for fname in files]
                file_dep = filter(os.path.isfile, file_dep)  # removes missing files
                task = {
                    'file_dep': list(file_dep),
                    'task_dep': ['copy_assets'],
                    'basename': str(self.name),
                    'name': str(output_path),
                    'actions': [(build_bundle, (name, files))],
                    'targets': [output_path],
                    'uptodate': [utils.config_changed(kw)],
                    'clean': True,
                }
                yield utils.apply_filters(task, kw['filters'])


def get_theme_bundles(themes):
    """Given a theme chain, return the bundle definitions."""
    bundles = {}
    for theme_name in themes:
        bundles_path = os.path.join(
            utils.get_theme_path(theme_name), 'bundles')
        if os.path.isfile(bundles_path):
            with open(bundles_path) as fd:
                for line in fd:
                    name, files = line.split('=')
                    files = [f.strip() for f in files.split(',')]
                    bundles[name.strip()] = files
                break
    return bundles
