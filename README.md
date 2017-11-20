Boston Crash Modeling
===================

Outline:
-----------------------
 - Project Vision
 - Connect
 - Getting Started
 - Project Organization


Project Vision
-----------------------
On Jan 25th, 2017, [9 pedestrians were hit in Boston by vehicles](http://www.bostonherald.com/news/local_coverage/2017/01/battle_for_safer_streets_nine_pedestrians_hit_in_boston_in_1_day). While this was a particularly dangerous day, there were 21 fatalities and over 4000 severe injuries due to crashes in 2016 alone, representing a public health issue for all those who live, work, or travel in Boston. The City of Boston would like to partner with Data For Democracy to help develop a dynamic prediction system that they can use to identify potential trouble spots to help make Boston a safer place for its citizens by targeting timely interventions to prevent crashes before they happen.

This is part of the City's long-term [Vision Zero initiative](http://www.visionzeroboston.org/), which is committed to the goal of zero fatal and serious traffic crashes in the city by 2030. The Vision Zero concept was first conceived in Sweden in 1997 and has been widely credited with a significant reduction in fatal and serious crashes on Sweden’s roads in the decades since then. Cities across the United States are adopting bold Vision Zero initiatives that share these common principles.

> Children growing up today deserve...freedom and mobility. Our seniors should be able to safely get around the communities they helped build and have access to the world around them. Driving, walking, or riding a bike on Boston’s streets should not be a test of courage.
>
> — Mayor Martin J. Walsh


Connect
-----------------------
Join our [Slack channel](https://datafordemocracy.slack.com/messages/p-boston-crash-model) on the D4D Slack. If you haven't joined our Slack yet, fill out [this contact form](http://datafordemocracy.org/contact.html)!

Leads:
 - D4D Project Lead: Ben Batorsky [@bpben](https://datafordemocracy.slack.com/messages/@bpben)
 - City of Boston Project Lead: Michelle Tat [@michelle_tat](https://datafordemocracy.slack.com/messages/@michelle_tat)

**Maintainers**: Maintainers have write access to the repository. They are responsible for reviewing pull requests, providing feedback and ensuring consistency.
 - [@bpben](https://datafordemocracy.slack.com/messages/@bpben)
 - [@michelle_tat](https://datafordemocracy.slack.com/messages/@michelle_tat)
 - [@therriault](https://datafordemocracy.slack.com/messages/@therriault)


Getting Started
-----------------------
### Contributing:
- **"First-timers" are welcome!** Whether you're trying to learn data science, hone your coding skills, or get started collaborating over the web, we're happy to help. If you have any questions feel free to pose them on our Slack channel, or reach out to one of the team leads. If you have questions about Git and GitHub specifically, our [github-playground repo](https://github.com/Data4Democracy/github-playground) and the [#github-help](https://datafordemocracy.slack.com/messages/github-help) Slack channel are good places to start.
- **Feeling comfortable with GitHub, and ready to dig in?** Check out our GitHub issues and projects. This is our official listing of the work that we are planning to get done.
- **This README is a living document:** If you see something you think should be changed, feel free to edit and submit a pull request. Not only will this be a huge help to the group, it is also a great first PR!
- **Got an idea for something we should be working on?** You can submit an issue on our GitHub page, mention your idea on Slack, or reach out to one of the project leads.

### Dependencies:
Most of the work on this project so far has been done in Python, in Jupyter notebooks.
- Python 2.7 (we recommend [Anaconda](https://www.continuum.io/downloads))
- conda (included with Anaconda)

### Environment:
You'll want to reproduce the packages and package versions required to run code in this repo, ideally in a virtual environment to avoid conflicts with other projects you may be working on. We've tested the environment.yml file on a Windows 64-bit machine and Linux and have done our best to ensure cross-platform compatibility, but if it doesn't work for you, please file an issue.

    $ conda env create -f environment.yml
    $ activate boston-crash-model

If you'd prefer to use a requirements.txt file, one is available in the [data_gen folder](https://github.com/Data4Democracy/boston-crash-modeling/tree/master/notebooks/data_generation) for spatial features analysis and in the [benchmark folder](https://github.com/Data4Democracy/boston-crash-modeling/tree/master/notebooks/benchmark) for running the benchmark model.

### Docker:
A basic Dockerfile has been created to run the project in a container, using the ContinuumIO anaconda base image (Python 2.7). Right now the container simply installs the project code & its dependencies, creates the 'boston-crash-model' virtual environment and starts an apache2 webserver (via supervisor daemon) to serve the visualization. A pre-built image is not yet available, to run the container execute the following from the project's root directory:

	$ docker build .
	$ docker run -d -p 8080:8080 --name bcm.local [id of image]

To view the visualization add an entry to your hosts file e.g:

	$ echo "bcm.local 127.0.0.1" | sudo tee -a /etc/hosts

and you should now be able to access the historical crash map via your browser at http://bcm.local:8080/visualization/historical_crash_map.html


### Data:

At the moment, the [RF benchmark model](https://github.com/Data4Democracy/boston-crash-modeling/blob/master/notebooks/benchmark/crash_predict_benchmark.ipynb) is running off of a dataset of historical crashes in 2016 per street segment + week. All our processed data is in a private repository in data.world [here](https://data.world/data4democracy/boston-crash-model) -- ping a project lead or maintainer on Slack to get access. More detailed documentation is contained there.

Data can be downloaded from the web frontend to data.world; it is expected to reside in the data directory.

At a high level, there are a variety of raw data sources available to us:
- Historical [crash data](http://app01.cityofboston.gov/VisionZero)
- Street segment inventories
- The Vision Zero crowdsourced [concerns map](http://app01.cityofboston.gov/VZSafety)
- [Other open city data](https://data.boston.gov/) (constituent requests, liquor licenses, assessing data)
-

Building off of [Vision Zero crash data](http://app01.cityofboston.gov/VisionZero) & the [Vision Zero concerns map](http://app01.cityofboston.gov/VZSafety).


Project Organization
-----------------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.testrun.org


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
