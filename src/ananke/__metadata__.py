#!/usr/bin/env python
"""
Contains the ananke module metadata.
"""
import _sitebuiltins
import textwrap
from typing import Final
from datetime import datetime

from . import _version

try:
    from .__license__ import __license_full__
except ImportError:
    __license_full__ = ""

__all__ = ['__project__', '__description__', '__url__', '__year__', '__author__', '__contributors__', '__license__',
           '__version__', '__date__', '__maintainer__', '__email__', '__classifiers__',
           '__credits__', '__doi__', '__citation__', '__adsurl__', '__bibtex__', '__copyright__', '__readme__',
           'copyright', 'credits', 'license', 'readme']

# PROJECT METADATA
__project__ = "py-ananke"
__description__ = "Provides a pipeline to generate mock synthetic star catalogs from star particle based simulated data."
__url__ = "https://github.com/athob/py-ananke"
__year__ = 2022
__author__ = "Adrien Thob"
__contributors__ = ["Robyn Sanderson", "Andrew Eden"]
__supporters__ = ["Farnik Nikakhtar", "Nondh Panithanpaisal", "Nicolas Garavito-Camargo", "Sanjib Sharma"]
__feedback__ = ["the extended Galaxy Dynamics @ UPenn group", "the participants of the \"anankethon\" workshops"]
__license__ = "GNU General Public License v3 or later (GPLv3+)"  # TODO change to longer version?
__license_classifier__ = "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
__license_short__ = "Licensed under the GNU GPL v3 or later"

# SOFTWARE METADATA
__version__: Final[str] = _version.get_versions()['version']
__date__: str = _version.get_versions()['date']
__date__: datetime = datetime.fromisoformat(f"{__date__[:-2]}:{__date__[-2:]}")
__maintainer__ = "Adrien Thob"
__email__ = "athob@sas.upenn.edu"
__status_classifier__ = "Development Status :: 5 - Production/Stable"
__classifiers__ = [
    __status_classifier__,
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    __license_classifier__,
    "Natural Language :: English",
    "Operating System :: Unix",
    "Programming Language :: Python :: 3",
    "Topic :: Scientific/Engineering :: Astronomy"
    ]

# CREDITS METADATA
__credits__ = textwrap.fill(f"""
Thanks to {', '.join(__contributors__)[::-1].replace(',','& ', 1)[::-1]} for their contributions,
to {', '.join(__supporters__)[::-1].replace(',','& ', 1)[::-1]} for their support & guidance,
and to the wider community for their suggestions and feedback,
including {', '.join(__feedback__)[::-1].replace(',','& ', 1)[::-1]}.
""".strip('\n'))

# CITING METADATA
__doi__ = "10.21105/joss.06234"
__citation__ = textwrap.fill("""
Thob, Adrien C. R. et al. 2024, “Generating synthetic star catalogs
from simulated data for next-gen observatories with py-ananke”,
The Journal of Open Source Software, 9, 6234, doi:10.21105/joss.06234.
""".strip('\n'))
__adsurl__ = "https://ui.adsabs.harvard.edu/abs/2024JOSS....9.6234T"
__adsexportcitation__ = f"{__adsurl__}/exportcitation"
__bibtex__ = """
@ARTICLE{2024JOSS....9.6234T,
       author = {{Thob}, Adrien C.~R. and {Sanderson}, Robyn E. and
       {Eden}, Andrew P. and {Nikakhtar}, Farnik and
       {Panithanpaisal}, Nondh and {Garavito-Camargo}, Nicol{\\'a}s
       and {Sharma}, Sanjib},
        title = "{Generating synthetic star catalogs from simulated data
        for next-gen observatories with py-ananke}",
      journal = {The Journal of Open Source Software},
     keywords = {C++, astronomy, galaxies, stars, simulations,
          mock observations, Jupyter Notebook, Python,
          Astrophysics - Astrophysics of Galaxies,
          Astrophysics - Instrumentation and Methods for Astrophysics},
         year = 2024,
        month = oct,
       volume = {9},
       number = {102},
          eid = {6234},
        pages = {6234},
          doi = {10.21105/joss.06234},
archivePrefix = {arXiv},
       eprint = {2312.02268},
 primaryClass = {astro-ph.GA},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2024JOSS....9.6234T},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
""".strip('\n')
__citing__ = '\n\n'.join(map(textwrap.fill, f"""
If {__project__} has played a role in your research project or software
development, we kindly request that you acknowledge and cite the
project. Citing {__project__} not only gives credit to the dedicated
efforts of its creators but also helps others discover and benefit
from this software.

To cite {__project__}, please use DOI {__doi__} as a
reference in your publications, or cite as the following:

{{__citation__}}

Alternatively, you may use one of the entries associated with
{__project__} as listed by The SAO/NASA Astrophysics Data System:
<{__adsexportcitation__}>
such as the following BibTeX entry:

{{__bibtex__}}
""".strip('\n').split('\n\n'))).format(__citation__=__citation__, __bibtex__=__bibtex__)

# COPYRIGHT METADATA
__copyright_short__ = f"Copyright (C) {__year__}-{__date__.year}  {__author__}"
__copyright__ = f"""
{textwrap.fill(f"{__project__} v{__version__}: {__description__}")}

{__copyright_short__}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

--CITING-------------------------------------------------------------

{__citing__}
""".strip('\n')

# README
__readme__ = f"""
{__copyright__}

--CREDITS------------------------------------------------------------

{__credits__}
""".strip('\n')

# DEFINING PRINTERS
copyright = _sitebuiltins._Printer('copyright', __copyright__)
credits = _sitebuiltins._Printer('credits', __credits__)
license = _sitebuiltins._Printer('license', __license_full__)
readme = _sitebuiltins._Printer('readme', __readme__)


if __name__ == '__main__':
    raise NotImplementedError()
