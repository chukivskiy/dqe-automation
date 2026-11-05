# Test Automation for DQE

## Fork project

Fork the repository into your own repository space.

## Containers

**docker-compose.yml** creates containers for PostgreSQL and Jenkins, all connected to the same network.

Compose using terminal in folder with docker-compsoe.yml file.

```
podman-compose up -d
```

If podman-compose is not installed:

```
pip install podman-compose
```

Check that the containers are running and connected to the same network:

```
podman ps
podman network inspect tafordqenetwork
```

## Access Jenkins

Open your browser and navigate to: http://localhost:8080

### Retrieve Initial Admin Password

From a file:

```
jenkins_home\secrets\initialAdminPassword
```

From logs:

```
podman logs jenkins | grep "Please use the following password"
```

### First initialization

1) Login using password from previous step to start initializing and click on “Install suggested plugins”.
2) Wait until all plugins are installed.
3) Create first admin user (remember credentials).

## Access PostgreSQL

PostgreSQL can be accessed:

* from local machine, port 5434;
* at postgres:5432 from other containers in the Podman network.

Credentials can be found in [docker-compose.yml](docker-compose.yml) file: services->postgres->environment.

## Run data pipeline

1. Create a New Pipeline Job:

* In Jenkins, click New Item.
* Select Pipeline and give it a name.
* Click OK.

2. Configure the Pipeline:

* Under Pipeline, select Pipeline script from SCM.
* Choose Git as the SCM.
* Enter the URL of your GitHub repository (e.g., https://github.com/your-username/your-repo.git).
* If the repository is private, add your GitHub credentials under Credentials.
* Specify the branch to use (e.g., main).
* Specify Script Path to Jenkins file: data_dev/Jenkinsfile. 

3. Build the Pipeline.

4. Verify result:

* Verify that the pipeline runs successfully without errors (Console output - logs).

* Enter Jenkins container.

```
podman exec -it jenkins /bin/bash
```

* Check that 3 folders are created and filled with parquet files inside:

Folders with files:

```markdown
parquet_data/
├── patient_sum_treatment_cost_per_facility_type/
│ └── ... (partitioned subdirectories with parquet files)
├── facility_name_min_time_spent_per_visit_date/
│ └── ... (partitioned subdirectories with parquet files)
└── facility_type_avg_time_spent_per_visit_date/
└── ... (partitioned subdirectories with parquet files)
```

Run PyTest Tests with EPAM ReportPortal

EPAM ReportPortal is used to monitor automated test execution, analyze failures, track test history, and visualize test results through dashboards.

1. Install dependencies

Navigate to the PyTest Introduction directory and activate the virtual environment.

cd "PyTest Introduction"
.\.venv\Scripts\Activate.ps1

Install the required packages:

python -m pip install pytest pytest-html pytest-reportportal

2. Configure ReportPortal

Open EPAM ReportPortal and log in using your EPAM account.

Navigate to Projects and find your personal project.

Open Profile → API Keys.

Generate an API key if you do not already have one.

Configure pytest.ini:

[pytest]
addopts = -v --html=reports/report.html --self-contained-html

markers =
    validate_csv: CSV validation tests
    unmarked: Tests without explicit markers

rp_endpoint = https://reportportal.epam.com
rp_project = ivan_chukivskyi_personal
rp_launch = DQE_Pytest_Homework
rp_launch_description = PyTest Introduction Homework
rp_verify_ssl = True
rp_log_level = INFO

Security: Do not commit your ReportPortal API key to GitHub.

Set the API key as an environment variable in PowerShell:

$env:RP_API_KEY = "YOUR_API_KEY"

Replace YOUR_API_KEY with your actual ReportPortal API key.

3. Execute tests

Run all PyTest tests and send results to ReportPortal:

python -m pytest ./tests --reportportal -v

The test results will be available in two locations:

Local HTML Report: reports/report.html

EPAM ReportPortal: https://reportportal.epam.com

4. Monitor test execution

Open EPAM ReportPortal.

Select the ivan_chukivskyi_personal project.

Navigate to Launches.

Find the DQE_Pytest_Homework launch.

Review Passed, Failed, Skipped, and Expected Failure test results.

Open failed test cases to inspect logs and stack traces.

Use Make Decision to classify failures by Defect Type.

5. Create a monitoring dashboard

Navigate to Launches and create a filter for DQE_Pytest_Homework.

Save the filter.

Navigate to Dashboards and create a new dashboard.

Add at least three widgets:

Overall statistics

Launch statistics chart

Most failed test cases

Apply the saved launch filter to each widget.

Use the dashboard to monitor test results and execution trends across multiple runs.

6. Verify results

Confirm that:

PyTest tests execute successfully.

Test results are uploaded to ReportPortal.

Failed tests contain logs and stack traces.

Defect Types can be assigned to failed tests.

The dashboard displays statistics from the selected launches.

* Check that report.html file is created:

```markdown
generated_report/
├── report.html
```
