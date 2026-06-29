def sample_analysis_result() -> dict:
    return {
        "job_details": {
            "job_title": "Data Engineer",
            "company_name": "Northstar Analytics",
            "salary_range": "$105,000 - $135,000",
            "location_or_work_policy": "Hybrid - New York, NY",
            "employment_type": "Full time",
            "job_link": "https://example.com/jobs/data-engineer",
            "sponsorship_policy": "Not specified",
            "experience_required": "3+ years",
            "degree_required": "Bachelor's degree or equivalent experience",
            "travel_requirement": "Not specified",
            "security_clearance": "Not required",
            "contract_or_full_time": "Full time",
        },
        "scores": {
            "overall_match_score": 78,
            "technical_match_score": 86,
            "ats_keyword_coverage_score": 81,
            "eligibility_score": 92,
            "experience_match_score": 74,
            "match_label": "Good Match",
        },
        "match_summary": {
            "headline": "Strong data engineering fit with a few proof gaps",
            "short_explanation": (
                "Your profile shows strong alignment with Python, SQL, PostgreSQL, streaming pipelines, "
                "dashboards, and production-minded data workflows. The main gaps are clearer evidence for "
                "cloud deployment ownership, orchestration depth, and measurable business impact."
            ),
            "apply_recommendation": "Apply after tailoring",
            "top_strengths": [
                "Python, SQL, PostgreSQL, Kafka, Docker, and dashboarding are clearly supported by project evidence.",
                "Fraud analytics and transaction streaming projects match common data engineering responsibilities.",
                "Monitoring-system work shows comfort with distributed services and operational visibility.",
            ],
            "top_concerns": [
                "Cloud implementation is mentioned, but project evidence should name the specific services used.",
                "Orchestration tools such as Airflow or Prefect are not clearly proven.",
                "Several bullets would be stronger with scale, latency, accuracy, or cost metrics.",
            ],
        },
        "jd_red_flags": [
            {
                "flag": "Cloud ownership is expected",
                "severity": "Medium",
                "jd_evidence": "Role asks for scalable data pipelines on cloud infrastructure.",
                "why_it_matters": "Hiring teams will expect evidence that the candidate can deploy and operate data workflows beyond local prototypes.",
                "candidate_impact": "Your profile should add one cloud-hosted pipeline or explain the deployment environment for an existing project.",
            }
        ],
        "jd_requirements": {
            "requirement_categories": [
                {"category": "Data Engineering", "requirements": ["ETL/ELT workflows", "SQL transformations", "data validation"], "candidate_status": "Strong"},
                {"category": "Streaming", "requirements": ["Kafka producers and consumers", "event validation", "pipeline monitoring"], "candidate_status": "Strong"},
                {"category": "Cloud", "requirements": ["Cloud deployment", "managed storage", "scheduled workloads"], "candidate_status": "Partial"},
                {"category": "Orchestration", "requirements": ["Workflow scheduling", "dependency management", "retry handling"], "candidate_status": "Partial"},
                {"category": "Business Impact", "requirements": ["Metrics", "stakeholder-ready dashboards", "prioritization"], "candidate_status": "Strong"},
            ],
            "must_have": [
                {
                    "requirement": "Build reliable ETL or ELT pipelines",
                    "status": "Supported",
                    "priority": "Important",
                    "recommendation": "Keep the fraud and streaming pipeline projects near the top of the resume.",
                    "resume_evidence": "Fraud analytics platform and credit-card transaction streaming pipeline.",
                },
                {
                    "requirement": "Write SQL for analytical datasets",
                    "status": "Supported",
                    "priority": "Important",
                    "recommendation": "Mention transformations, validation checks, and downstream reporting tables.",
                    "resume_evidence": "SQL transformations and PostgreSQL loading are explicitly included.",
                },
                {
                    "requirement": "Deploy or operate pipelines in a cloud environment",
                    "status": "Partial",
                    "priority": "Would help",
                    "recommendation": "Add one AWS, Azure, or GCP deployment detail if true.",
                    "resume_evidence": "Docker and pipeline services are shown, but cloud services are not named.",
                },
            ],
            "nice_to_have": [
                {
                    "requirement": "Workflow orchestration with Airflow or Prefect",
                    "status": "Missing",
                    "priority": "Would help",
                    "recommendation": "Add a small scheduled DAG around an existing pipeline.",
                    "resume_evidence": "No orchestration tool is named in the supplied projects.",
                },
                {
                    "requirement": "Observability dashboards",
                    "status": "Supported",
                    "priority": "Nice to have",
                    "recommendation": "Connect monitoring dashboards to reliability outcomes.",
                    "resume_evidence": "Grafana and InfluxDB dashboards for ingestion volume, latency, errors, and health.",
                },
            ],
            "job_title_requirements": [
                {
                    "requirement": "Data Engineer title alignment",
                    "status": "Supported",
                    "recommendation": "Use a target title such as Data Engineer or Data Platform Engineer.",
                    "resume_evidence": "Projects center on pipelines, SQL stores, streaming, and monitoring.",
                }
            ],
        },
        "skills_analysis": {
            "matched_skills": [
                {"skill": "Python", "evidence": "Fraud analytics and Kafka pipeline projects."},
                {"skill": "SQL", "evidence": "SQL transformations and PostgreSQL loading."},
                {"skill": "Kafka", "evidence": "Real-time transaction streaming pipeline."},
                {"skill": "PostgreSQL", "evidence": "Fraud analytics and streaming storage."},
                {"skill": "Docker", "evidence": "Containerized pipeline and monitoring services."},
            ],
            "missing_skills": [
                {"skill": "Airflow or Prefect", "importance": "Would help", "recommendation": "Schedule the streaming or fraud pipeline with retries and dependency checks."},
                {"skill": "Named cloud services", "importance": "Would help", "recommendation": "Deploy one project to AWS, Azure, or GCP and cite the services."},
                {"skill": "Data quality framework", "importance": "Nice to have", "recommendation": "Add validation checks with Great Expectations or dbt tests."},
            ],
            "nice_to_have_skills": [
                {"skill": "dbt", "evidence": "Not shown; useful for SQL transformation workflows."},
                {"skill": "Terraform", "evidence": "Not shown; useful for cloud infrastructure evidence."},
            ],
        },
        "ats_keyword_coverage": [
            {"keyword": "Python", "coverage_status": "Covered", "importance": "Important", "resume_evidence": "Used across fraud analytics and streaming pipeline projects."},
            {"keyword": "SQL", "coverage_status": "Covered", "importance": "Important", "resume_evidence": "SQL transformations and PostgreSQL loading."},
            {"keyword": "Kafka", "coverage_status": "Covered", "importance": "Important", "resume_evidence": "Kafka producers and consumers in transaction pipeline."},
            {"keyword": "Cloud", "coverage_status": "Partial", "importance": "Would help", "resume_evidence": "Cloud is not proven with named services."},
            {"keyword": "Airflow", "coverage_status": "Missing", "importance": "Would help", "resume_evidence": "No orchestration tool mentioned."},
            {"keyword": "Dashboarding", "coverage_status": "Covered", "importance": "Nice to have", "resume_evidence": "Power BI, Streamlit, Grafana dashboards."},
        ],
        "ats_score_breakdown": [
            {"category": "Core Skills", "score": 86, "status": "Strong", "evidence": "Python, SQL, Kafka, PostgreSQL, Docker.", "recommendation": "Keep these near the top of the resume."},
            {"category": "Cloud Evidence", "score": 58, "status": "Partial", "evidence": "No named cloud services in projects.", "recommendation": "Add one cloud deployment detail if true."},
            {"category": "Impact Metrics", "score": 66, "status": "Partial", "evidence": "Dashboards and prioritization are present, but metrics are limited.", "recommendation": "Add scale, latency, error-rate, or accuracy metrics."},
        ],
        "eligibility_risks": [],
        "evidence_based_matches": [
            {"requirement": "Real-time data processing", "match_strength": "Strong", "explanation": "The Kafka transaction pipeline directly supports this requirement.", "resume_evidence": "Kafka producers/consumers, event validation, rejected-record handling."},
            {"requirement": "Analytical reporting", "match_strength": "Strong", "explanation": "The fraud analytics platform includes dashboards for investigation workflows.", "resume_evidence": "Power BI/Streamlit dashboards for suspicious transaction prioritization."},
            {"requirement": "Operational monitoring", "match_strength": "Strong", "explanation": "The server monitoring system shows production-awareness.", "resume_evidence": "Go, NATS, InfluxDB, Docker metrics pipeline."},
        ],
        "hallucination_guardrail": [
            {"claim_or_skill": "AWS production deployment", "status": "Missing", "evidence": "No specific AWS service or deployment is provided.", "action": "Do not claim production AWS deployment unless it is true."},
            {"claim_or_skill": "Airflow orchestration", "status": "Missing", "evidence": "No Airflow project or DAG is listed.", "action": "Add a project first or leave it out."},
        ],
        "before_after_bullets": [
            {
                "original": "Built a streaming transaction pipeline with Kafka and PostgreSQL.",
                "rewritten": "Built a Kafka-based credit-card transaction pipeline with event validation, rejected-record handling, PostgreSQL loading, and Grafana monitoring for ingestion volume, latency, and errors.",
                "why_improved": "Adds architecture, reliability checks, storage target, and observability evidence without inventing unsupported claims.",
                "evidence_status": "Supported",
            },
            {
                "original": "Designed a fraud analytics platform.",
                "rewritten": "Designed a fraud analytics platform that used SQL transformations, behavioral risk features, and ML classification to help investigators prioritize suspicious financial transactions.",
                "why_improved": "Clarifies the business workflow and technical contribution.",
                "evidence_status": "Supported",
            },
        ],
        "resume_timeline_check": [
            {"issue": "Timeline detail is light", "severity": "Low", "evidence": "Projects are listed without dates.", "recommendation": "Add project dates or mark them as portfolio projects if appropriate."}
        ],
        "resume_fix_suggestions": [
            {"issue": "Cloud proof is thin", "priority": "Would help", "why_it_matters": "Cloud appears in many data engineering JDs.", "suggested_fix": "Deploy one project to AWS, Azure, or GCP and cite named services."},
            {"issue": "Metrics need sharper outcomes", "priority": "Important", "why_it_matters": "Recruiters scan for measurable impact.", "suggested_fix": "Add transaction volume, latency, model performance, dashboard users, or error reduction where accurate."},
            {"issue": "Orchestration is absent", "priority": "Would help", "why_it_matters": "Scheduling and retries signal production readiness.", "suggested_fix": "Add Airflow or Prefect to one pipeline project."},
        ],
        "skill_gap_learning_plan": [
            {"skill": "Airflow", "priority": "Would help", "why_needed": "Many pipeline roles expect workflow scheduling.", "learning_action": "Create a DAG around the streaming pipeline with retries and alerts.", "mini_project_idea": "Scheduled fraud-feature build with daily validation."},
            {"skill": "Cloud storage and compute", "priority": "Would help", "why_needed": "The JD expects cloud-ready pipelines.", "learning_action": "Deploy a small data pipeline on one cloud provider.", "mini_project_idea": "S3 or Azure Blob ingestion with scheduled transforms."},
        ],
        "project_suggestions": [
            {"project_title": "Cloud Fraud Data Lake Pipeline", "priority": "Important", "target_gap": "Cloud deployment and orchestration", "why_it_helps": "Extends an existing fraud project into a cloud-ready data engineering story.", "suggested_scope": "Ingest CSV transactions, validate schema, transform features, store curated tables, and monitor pipeline health.", "resume_bullet_example": "Deployed a cloud-hosted fraud data lake pipeline with scheduled validation, curated SQL-ready tables, and monitoring for ingestion failures."},
            {"project_title": "Airflow Transaction Quality DAG", "priority": "Would help", "target_gap": "Workflow orchestration", "why_it_helps": "Shows scheduling, retries, and dependency management.", "suggested_scope": "Wrap the Kafka/PostgreSQL pipeline with daily data quality checks and failure notifications.", "resume_bullet_example": "Built an Airflow DAG to orchestrate transaction quality checks, retry failed loads, and surface pipeline health metrics."},
        ],
        "certification_suggestions": [
            {"certification": "AWS Certified Cloud Practitioner", "priority": "Nice to have", "target_gap": "Cloud fundamentals", "why_it_helps": "Gives baseline cloud vocabulary for interviews.", "estimated_effort": "2-4 weeks"},
            {"certification": "Google Professional Data Engineer or Azure Data Engineer Associate", "priority": "Would help", "target_gap": "Cloud data engineering", "why_it_helps": "Signals deeper cloud data-platform readiness.", "estimated_effort": "6-10 weeks"},
        ],
        "tailored_resume_content": {
            "tailored_summary": "Data engineering candidate with hands-on Python, SQL, Kafka, PostgreSQL, Docker, and dashboarding experience across fraud analytics, transaction streaming, and distributed monitoring projects.",
            "rewritten_bullets": [
                {"rewritten": "Built a Kafka-based transaction streaming pipeline with event validation, rejected-record handling, PostgreSQL loading, and Grafana dashboards for ingestion volume, latency, errors, and health.", "evidence_status": "Supported"},
                {"rewritten": "Designed a fraud analytics platform using SQL transformations, behavioral risk features, ML classification, and investigation dashboards to prioritize suspicious transactions.", "evidence_status": "Supported"},
            ],
        },
        "cover_letter": "",
    }
