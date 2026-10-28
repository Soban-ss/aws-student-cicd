# Real AWS CI/CD Student Management System

A working Flask CRUD app using SQLAlchemy with PostgreSQL on RDS for AWS and SQLite for local development. GitHub -> CodePipeline Source -> CodeBuild tests -> Elastic Beanstalk deploy. The database is separate from Elastic Beanstalk, so deployment does not erase records.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python application.py
```

Open http://127.0.0.1:5000. SQLite is used locally if DATABASE_URL is not set.

## AWS setup (console; choose one region for everything)

**Warning:** RDS and Elastic Beanstalk EC2 resources can incur charges. Delete them after the lab. Avoid putting secrets in GitHub or screenshots.

1. **GitHub:** Create a new repository and upload all project files, including `buildspec.yml`, `Procfile`, and `.ebextensions/`. Do not upload `.env` or database files.
2. **RDS PostgreSQL:** Create a PostgreSQL database instance. Set initial database name `studentdb`. Choose an affordable instance class; note the endpoint, port 5432, master username and password. Prefer private database access. For a simple lab, create RDS in the same VPC as Elastic Beanstalk and allow inbound PostgreSQL TCP 5432 **only from the Elastic Beanstalk EC2 instance security group**, not from 0.0.0.0/0. Set DB public accessibility to No. Ensure the EB instance security group can reach the DB.
3. **Elastic Beanstalk:** Create application `student-management` and environment `student-management-env`, platform **Python 3.11** on Amazon Linux 2023 if available, single instance for a lab. Configure service and EC2 instance roles using the console's recommended roles and required policies. Set environment variables `DATABASE_URL` to `postgresql+psycopg2://USER:PASSWORD@RDS_ENDPOINT:5432/studentdb` and `SECRET_KEY` to a random long string. For production, use Secrets Manager or supported secrets integration instead of plain environment values. If password has URL-reserved characters, percent-encode it in the URL. Use the repository's `Procfile` for Gunicorn startup. Upload a source bundle to create the environment initially, or use a sample application until pipeline deploys the first version. If using a source bundle, zip **the contents** of the project directory, not its parent directory.
4. **CodeBuild:** Create build project `student-management-build`, managed image Amazon Linux, standard runtime supporting Python 3.11, buildspec from source (`buildspec.yml`), and a suitable service role. Use the smallest supported compute configuration. Do not enable privileged mode. CodeBuild runs pytest and produces the deployable artifact.
5. **CodePipeline:** Create pipeline `student-management-pipeline`. Source provider **GitHub (via GitHub App connection)**; select repository and `main` branch. Enable push-trigger changes. Build provider **AWS CodeBuild**, select `student-management-build`, and ensure build input is source artifact. Deploy provider **AWS Elastic Beanstalk**, select `student-management` and `student-management-env`, and use the CodeBuild output artifact as deploy input. Let the console create or configure the appropriate IAM service roles.
6. **Run and verify:** Push a commit. CodePipeline should show Source, Build and Deploy successful. Open the Elastic Beanstalk environment URL and add a student. Refresh to confirm persistence. Edit the heading in `templates/index.html`, commit and push; watch the new pipeline execution complete. Refresh the live URL and verify the changed heading and existing student records.
7. **Failure demo:** Temporarily introduce a failing assertion in a test, commit and push, and show CodeBuild failing. The deploy stage must not run for that execution. Restore the test, push and verify the pipeline succeeds.

## Troubleshooting

- **CodeBuild says concurrency quota 0 or capacity error:** Check the exact environment type, region and quota; a quota increase to 1 may not cover the selected compute type. Try a supported small managed environment, or contact AWS Support for account-level capacity restrictions.
- **Elastic Beanstalk unhealthy:** Inspect EB events and logs. Confirm Python platform, `Procfile`, RDS connection, instance IAM role and security group rules.
- **Database connection fails:** Confirm endpoint, username, password, `studentdb`, VPC routing, and inbound 5432 from EB security group. RDS must be available before EB starts because the application initializes its tables at import time.
- **Pipeline source fails:** Check GitHub connection authorization, branch, and trigger configuration.
- **Build fails:** Open CodeBuild logs in CloudWatch and inspect install/test output.
- **SSM agent access denied:** SSM access is not required for a standard EB deployment. Configure an appropriate instance profile/SSM role separately only if you need Session Manager access.

## Architecture / security notes

This is an educational CRUD application without user authentication or CSRF protection. Do not publish real personal student information or use it for production. For a public deployment, add login/authentication, CSRF protection, HTTPS and secure secrets management. RDS is intentionally external to the EB environment. Delete the pipeline, EB environment, RDS instance and related resources after the demonstration to avoid ongoing costs.
