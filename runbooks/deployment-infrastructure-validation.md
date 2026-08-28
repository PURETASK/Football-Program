# Deployment Infrastructure Validation

Run `PYTHONPATH=src python scripts/validate_deployment_infrastructure.py` to validate the repository Dockerfile against `deployment/nfl-fidos-deployment.json`. The check covers the base image family, package and media-tool installation, runtime command, healthcheck, port, persistent volume, and declared environment keys.

This is a static contract check. It does not build an image, contact a registry, deploy a service, use production secrets, or enable production. A real image build and provider deployment remain separate deployment-owner actions.
