# `py-ananke`

[![Documentation Status](https://readthedocs.org/projects/py-ananke/badge/?version=latest)](https://py-ananke.readthedocs.io/en/latest/?badge=latest)
[![Python package](https://github.com/athob/py-ananke/actions/workflows/main.yml/badge.svg)](https://github.com/athob/py-ananke/actions/workflows/main.yml)
[![status](https://joss.theoj.org/papers/357c0445d891fc10e1b0ca4dba1e3cc0/status.svg)](https://joss.theoj.org/papers/357c0445d891fc10e1b0ca4dba1e3cc0)
[![arXiv](https://img.shields.io/badge/arXiv-2312.02268-b31b1b.svg?style=flat)](https://arxiv.org/abs/2312.02268)
[![DOI](https://zenodo.org/badge/498927304.svg)](https://zenodo.org/badge/latestdoi/498927304)

Welcome to `py-ananke`, a Python package that offers `ananke` which is a comprehensive pipeline designed to generate mock astrometric and photometric catalogs of synthetic stars derived from particle-based simulated star populations.

## Project genesis

[![GAIA mock star survey from FIRE](https://bpb-us-e1.wpmucdn.com/sites.northwestern.edu/dist/6/84/files/2018/06/m12f-lsr1-threecolor-medfilt-crop-50-28irpjo.png)](https://fire.northwestern.edu/ananke/)
*RGB flux map of a synthetic survey of the FIRE-2 simulated galaxy m12f (image credit: [Sanderson et al. 2020](https://ui.adsabs.harvard.edu/abs/2020ApJS..246....6S/abstract)).*

The package was designed to provide easy installation and distribution of the `ananke` software, as described in [Sanderson et al. 2020](https://ui.adsabs.harvard.edu/abs/2020ApJS..246....6S/abstract). In this work, the team focused on cosmological simulations, such as the latte suite of FIRE simulations which have limited resolution and cannot accurately represent fully resolved stellar populations with individual stars. To address this challenge, the authors of `ananke` developed a framework consisting of scripts and data that enabled the generation of synthetic GAIA star surveys from these simulated galaxies. The framework combines density estimations and IMF sampling techniques to create representative populations of mock stars.

An essential aspect of `ananke` is its integration with the [`EnLink`](https://ui.adsabs.harvard.edu/abs/2009ApJ...703.1061S/abstract)/[`EnBiD`](http://ascl.net/1109.012) C++ software for computing phase space densities. These computed densities are then used as input for the [`Galaxia`](http://ascl.net/1101.007) C++ software, which generates synthetic surveys by incorporating user-supplied GAIA isochrones to produce the mock photometry.

The development of `py-ananke` aims to make this sophisticated framework accessible to a broader community. By providing a self-contained and easily installable Python package, we strive to facilitate the usage and adoption of `ananke` for generating mock star surveys from cosmological simulations, enabling the investigation of stellar halos around nearby galaxies.

## Getting started

`py-ananke` is compatible with Python versions above 3.7.12 and below 3.11. The project is organized into three branches: [main](https://github.com/athob/py-ananke/tree/main), [stable](https://github.com/athob/py-ananke/tree/stable), and [develop](https://github.com/athob/py-ananke/tree/develop). The main branch contains the latest released version, while the stable and develop branches host versions currently in development, with stable being the most recent stable version. `py-ananke` uses dedicated wrapper submodules, namely [`py-EnBiD-ananke`](https://github.com/athob/py-EnBiD-ananke) and [`py-Galaxia-ananke`](https://github.com/athob/py-Galaxia-ananke), specifically developed to handle the installation and utilization of the C++ backend software, [`EnBiD`](http://ascl.net/1109.012), and a modified version of [`Galaxia`](http://ascl.net/1101.007) called [`galaxia-ananke`](https://github.com/athob/galaxia-ananke). These submodules relieve users from the need to directly manage the C++ software while isolating the C++ wrapping process. This allows `py-ananke` to focus on processing inputs and outputs using pure Python. It is worth noting that [`galaxia-ananke`](https://github.com/athob/galaxia-ananke) incorporates several pre-installed photometric systems, represented by sets of isochrones generated from the [CMD web interface](http://stev.oapd.inaf.it/cgi-bin/cmd) (commonly referred to as Padova isochrones). Among the available options are HST, GAIA, Euclid, Rubin, JWST & Roman.

### Installation

To install `py-ananke`, you can use the following pip command, which pulls the latest version directly from the repository's main branch:

    pip install git+https://github.com/athob/py-ananke@main

or

    python -m pip install git+https://github.com/athob/py-ananke@main

Alternatively, if you prefer, you may clone the repository to your local machine and then install `py-ananke` using the following pip command, which installs it from your local copy of the repository:

    git clone https://github.com/athob/py-ananke
    cd py-ananke
    pip install .

Please note that the command with flag `pip install . --no-cache-dir` may be necessary due to some dependencies issues.

***Warning: DO NOT download the repository as a ZIP archive with intention to install it this way, the installation requires the git set up of the repository to propertly install its submodule dependencies.***

After installation, the module can be imported in Python under the name `ananke` and be ran as such.

### Simplified use case

The repository includes a Jupyter notebook that demonstrates a simplified use case utilizing a dummy set of randomly generated particle data. You can access the notebook directly at [jupyter/example_notebook.ipynb](jupyter/example_notebook.ipynb). This notebook provides a step-by-step example to help you understand the functionality and usage of `py-ananke` in a straightforward manner.

Note that you will need Jupyter installed on the machine where you intend to test this notebook, which will not be automatically installed by the `py-ananke`'s installation as it is not required to run its modules. Please follow the [Project Jupyter dedicated instructions](https://jupyter.org/install) for installing its tools such as [JupyterLab](https://jupyter.org/install#jupyterlab) or [Jupyter Notebook](https://jupyter.org/install#jupyter-notebook).

## What's under the hood

Work in progress...

## On-going development

`py-ananke` is now [published in The Journal of Open Source Software](https://joss.theoj.org/papers/10.21105/joss.06234). You can also access the associated arXiv publication [here](https://arxiv.org/abs/2312.02268).

### Upcoming updates

We have an exciting roadmap of upcoming updates planned, which we aim to implement prior to or following the submission. Here are some of the planned updates in no particular order:

- **Improving Extinction**: The extinction feature is currently in an experimental state, and we have identified areas for significant improvement. Firstly, while the user can supply their own extinction coefficients Aλ/A0 for any photometric system, only GAIA currently has default coefficients. Future updates will expand the range of default extinction coefficients for different systems. Secondly, the estimation of dust column density maps per particle currently requires user input. Our plan is to incorporate a treatment that directly computes dust column densities from the simulated metal-enriched gas provided by the user.
- **Implementing Error Modelling**: The original `ananke` framework ([Sanderson et al. 2020](https://ui.adsabs.harvard.edu/abs/2020ApJS..246....6S/abstract)) featured error modelling as a significant component. In future updates, we will introduce a framework that allows for the incorporation of simple error models into the pipeline, enhancing the robustness of the generated mock surveys.
- **Interfacing with Isochrone Databases**: `py-ananke` currently includes pre-loaded isochrones for a chosen photometric system (some of which are listed in the introduction section). Our plan is to implement a direct interface with established isochrone databases such as [Padova](http://stev.oapd.inaf.it/cgi-bin/cmd) or [MIST](https://waps.cfa.harvard.edu/MIST/), enabling users to download available photometric systems on-the-fly. Additionally, we aim to develop a framework that allows `py-ananke` to output photometry in a range of commonly used calibration standards.
- **Additional Modularization**: While [`EnBiD`](http://ascl.net/1109.012) serves as the density estimation routine of choice, we plan to expand the options by adding more choices such as [`EnLink`](https://ui.adsabs.harvard.edu/abs/2009ApJ...703.1061S/abstract). Furthermore, we intend to diversify the selection of kernel functions for density estimation and sampling mock stars in phase space, making it possible to utilize anisotropic kernel functions. Additionally, we will enhance the flexibility of `py-ananke` by incorporating a wider range of initial mass functions (IMFs) and allowing mass sampling based on present mass functions, particularly for generating mock stars in globular clusters.
- **Quality of Life Updates**: We are dedicated to enhancing the user experience and overall usability of `py-ananke`. To that end, we will be implementing various quality of life updates, refining the software interface, improving documentation, and streamlining the overall workflow.

These upcoming updates signify our commitment to continuously improve `py-ananke` and address the evolving needs of the community. We encourage users to stay engaged with the project, provide feedback, and contribute to its development as we work towards a more comprehensive and user-friendly tool for generating mock surveys.

### Contributing

You can readily access the code in the [main GitHub repository](https://github.com/athob/py-ananke), as well as its submodules repositories. We encourage users to utilize the [Github issues](https://github.com/athob/py-ananke/issues) feature to report any bugs encountered or suggest new ideas for improvement. Contributions to the project are highly valued and greatly appreciated. To contribute, we kindly request that you make your changes in a separate branch or fork of the repository. Once your contributions are ready, you can submit a [pull request](https://github.com/athob/py-ananke/pulls) to merge them into the [develop](https://github.com/athob/py-ananke/tree/develop) branch. If you choose to make your contributions in a fork, please make sure to base those changes from the develop branch in that fork, and have your pull requests originate from your forked develop branch and target this repository's develop branch. Additionally, you may need to confirm that the Workflow permissions in your fork settings are set to Read and write (Settings > Actions > General > Workflow permissions) in case the [CI/CD GitHub Action](https://github.com/athob/py-ananke/actions/workflows/main.yml) doesn't complete.

## `py-ananke` & the community

### License

`py-ananke` is distributed under the [GNU General Public License (GPL) version 3](LICENSE), offering you the freedom to utilize, modify, and distribute the software. The GPL v3 ensures that you have the flexibility to adapt py-ananke to suit your specific needs, while also contributing to the open-source community. We encourage you to read the full license text to understand your rights and responsibilities when using py-ananke.

### Citing `py-ananke`

If py-ananke has played a role in your research project or software development, we kindly request that you acknowledge and cite the project. Citing py-ananke not only gives credit to the dedicated efforts of its creators but also helps others discover and benefit from this software.

To cite `py-ananke`, please use DOI `10.21105/joss.06234` as a reference in your publications, or cite as the following:

```text
Thob, Adrien C. R. et al. 2024, “Generating synthetic star catalogs from simulated data for next-gen observatories with py-ananke”, The Journal of Open Source Software, 9, 6234, doi:10.21105/joss.06234.
```

Alternatively, you may use [one of the entries associated with `py-ananke` as listed by The SAO/NASA Astrophysics Data System](https://ui.adsabs.harvard.edu/abs/2023arXiv231202268T/exportcitation), such as the following BibTeX entry:

```text
@ARTICLE{2024JOSS....9.6234T,
       author = {{Thob}, Adrien and {Sanderson}, Robyn and {Eden}, Andrew and {Nikakhtar}, Farnik and {Panithanpaisal}, Nondh and {Garavito-Camargo}, Nicol{\'a}s and {Sharma}, Sanjib},
        title = "{Generating synthetic star catalogs from simulated data for next-gen observatories with py-ananke}",
      journal = {The Journal of Open Source Software},
     keywords = {C++, astronomy, galaxies, stars, simulations, mock observations, Jupyter Notebook, Python, Astrophysics - Astrophysics of Galaxies, Astrophysics - Instrumentation and Methods for Astrophysics},
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
```

### Dissemination

Below, you will find a selection of scientific papers that showcase the potential and capabilities of py-ananke. These papers serve as valuable resources for understanding the practical implementation and impact of py-ananke in various domains.

- Gray et al. 2024, “EDGE: A new model for Nuclear Star Cluster formation in dwarf galaxies”, arXiv e-prints, arXiv:2405.19286, [doi:10.48550/arXiv.2405.19286](https://arxiv.org/pdf/2405.19286)

`py-ananke` has also been discussed extensively in various workshops and conferences.

- [`py-ananke_v0.0.2-beta2`](https://github.com/athob/py-ananke/releases/tag/v0.0.2-beta2) was featured at [EAS 2023 in Krakow](https://eas2023programme.kuoni-congress.info/presentation/generating-mock-euclid-and-roman-surveys-of-stellar-halos-of-simulated-nearby-galaxies-using-the-py-ananke-pipeline) as an e-poster, check it at [this URL](https://k-poster.kuoni-congress.info/eas-2023/poster/5bf40113-efa9-4bfc-89a5-b67ebd81f7dd).
- [`py-ananke_v0.1.0-beta2`](https://github.com/athob/py-ananke/releases/tag/v0.1.0-beta2) was featured at the 243rd AAS meeting in New Orleans.
- a Galactic Plane survey application of `py-ananke` was featured at:
    1. the [Roman@Yerkes workshop on Galactic Science with the Nancy Grace Roman Space Telescope](https://sites.google.com/cfa.harvard.edu/romanyerkes/home),
    2. [EAS 2024 in Padova](https://eas2024programme.kuoni-congress.info/presentation/synthetic-survey-catalogs-for-the-galactic-roman-infrared-plane-survey-grips-using-py-ananke) as an e-poster (available [here](https://k-poster.kuoni-congress.info/eas-2024/poster/749fd8f1-ec4c-4167-911f-914e2215eeab)),
    3. the [Challenging Theory with Roman meeting at Caltech](https://conference.ipac.caltech.edu/roman2024/) (recording available [here](https://youtu.be/93hF1ZCDzw8)),
    4. the [2024 IAU GA in Cape Town](https://astronomy2024.org/) (live streamed [here](https://m.youtube.com/watch?v=8R-Wc9tGWcg&t=7218s)).

## Acknowledgements

We extend our sincere gratitude to [Robyn Sanderson (UPenn)](https://live-sas-physics.pantheon.sas.upenn.edu/people/standing-faculty/robyn-sanderson), [Andrew Eden (FloridaTech)](mailto:Andrew%20Eden%20<aeden2019@my.fit.edu>), [Farnik Nikakhtar (Yale)](https://physics.yale.edu/people/farnik-nikakhtar), [Nondh Panithanpaisal (UPenn/CarnegieObs)](https://nonsk131.github.io), and [Nicolas Garavito-Camargo (FlatironCCA)](https://jngaravitoc.github.io/Garavito-Camargo/) for their invaluable contributions and support during the development of this package. Their expertise, guidance, and collaboration have been instrumental in shaping the vision and advancement of this project. We also appreciate the valuable feedback and suggestions provided by the wider community, including the extended [Galaxy Dynamics @ UPenn group](https://web.sas.upenn.edu/dynamics/) and the participants of the "anankethon" workshop, which have significantly contributed to the refinement and enhancement of the package.
