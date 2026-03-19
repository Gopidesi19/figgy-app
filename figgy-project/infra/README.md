# Infrastructure as Code (IaC)

This directory is intended to house all Infrastructure as Code (IaC) definitions for deploying the Figgy microservices to Google Cloud Platform.

## Technologies

-   **Terraform**: For provisioning and managing cloud resources.

## Structure

-   `terraform/`: Contains Terraform configuration files (`.tf`) for defining the GCP infrastructure.

## Deployment Steps (Conceptual)

1.  **Initialize Terraform**: `terraform init`
2.  **Plan Changes**: `terraform plan`
3.  **Apply Changes**: `terraform apply`

This would typically provision:

-   Google Cloud Project (if not already existing)
-   Firestore Database
-   Pub/Sub Topics (e.g., `orders.place`, `orders.created`, `orders.accepted`, `orders.rejected`)
-   Cloud Run Services (User Service, Order Processor, Restaurant Service)
-   Cloud Functions (Delivery Orchestrator, Delivery Completion Service)
-   Cloud Tasks Queue
-   IAM Roles and Permissions
-   API Gateway configuration
