import json


RESOURCE_MAP = {

    "Spring Boot": {
        "group": "Spring Ecosystem",
        "priority": 1,
        "learn": {
            "type": "Documentation",
            "title": "Spring Boot Documentation",
            "url": "https://docs.spring.io/spring-boot/index.html"
        },
        "practice": "Build a CRUD REST API using Spring Boot.",
        "project": "Student Management REST API"
    },

    "Spring MVC": {
        "group": "Spring Ecosystem",
        "priority": 2,
        "learn": {
            "type": "Documentation",
            "title": "Spring Web MVC Documentation",
            "url": "https://docs.spring.io/spring-framework/reference/web/webmvc.html"
        },
        "practice": "Create controllers, request mappings and REST endpoints.",
        "project": "Employee Management API"
    },

    "Spring": {
        "group": "Spring Ecosystem",
        "priority": 2,
        "learn": {
            "type": "Documentation",
            "title": "Spring Framework Documentation",
            "url": "https://docs.spring.io/spring-framework/reference/"
        },
        "practice": "Learn Dependency Injection and Spring Beans.",
        "project": "Simple Spring Dependency Injection Application"
    },

    "Hibernate": {
        "group": "Database",
        "priority": 3,
        "learn": {
            "type": "Documentation",
            "title": "Hibernate Documentation",
            "url": "https://hibernate.org/orm/documentation/"
        },
        "practice": "Create entities and perform CRUD operations.",
        "project": "Student Database Application"
    },

    "JPA": {
        "group": "Database",
        "priority": 3,
        "learn": {
            "type": "Documentation",
            "title": "Jakarta Persistence Documentation",
            "url": "https://jakarta.ee/specifications/persistence/"
        },
        "practice": "Create entities, repositories and relationships.",
        "project": "Course Management API"
    },

    "Database Design": {
        "group": "Database",
        "priority": 3,
        "learn": {
            "type": "Documentation",
            "title": "Database Design Fundamentals",
            "url": "https://www.postgresql.org/docs/"
        },
        "practice": "Design tables, primary keys, foreign keys and relationships.",
        "project": "Design a placement management database."
    },

    "JUnit": {
        "group": "Testing",
        "priority": 4,
        "learn": {
            "type": "Documentation",
            "title": "JUnit 5 User Guide",
            "url": "https://junit.org/junit5/docs/current/user-guide/"
        },
        "practice": "Write unit tests for Java methods.",
        "project": "Add unit tests to a Java REST API."
    },

    "Mockito": {
        "group": "Testing",
        "priority": 4,
        "learn": {
            "type": "Documentation",
            "title": "Mockito Documentation",
            "url": "https://javadoc.io/doc/org.mockito/mockito-core/latest/org.mockito/org/mockito/Mockito.html"
        },
        "practice": "Mock service and repository dependencies.",
        "project": "Unit test a Spring Boot service using Mockito."
    },

    "Collections": {
        "group": "Java Core",
        "priority": 1,
        "learn": {
            "type": "Documentation",
            "title": "Java Collections Framework",
            "url": "https://docs.oracle.com/en/java/javase/"
        },
        "practice": "Practice ArrayList, HashMap, HashSet, Queue and Stack.",
        "project": "Build a Java contact management application."
    },

    "Multithreading": {
        "group": "Java Core",
        "priority": 1,
        "learn": {
            "type": "Documentation",
            "title": "Java Concurrency",
            "url": "https://docs.oracle.com/en/java/javase/"
        },
        "practice": "Practice threads, Runnable, synchronization and executors.",
        "project": "Build a multithreaded task processor."
    },

    "Exception Handling": {
        "group": "Java Core",
        "priority": 1,
        "learn": {
            "type": "Documentation",
            "title": "Java Exceptions",
            "url": "https://docs.oracle.com/en/java/javase/"
        },
        "practice": "Practice try-catch, custom exceptions and finally.",
        "project": "Build a banking application with custom exceptions."
    },

    "REST APIs": {
        "group": "Backend",
        "priority": 5,
        "learn": {
            "type": "Documentation",
            "title": "Spring REST Documentation",
            "url": "https://spring.io/guides/gs/rest-service/"
        },
        "practice": "Build GET, POST, PUT and DELETE endpoints.",
        "project": "Build a Student REST API."
    },

    "Microservices": {
        "group": "Backend",
        "priority": 6,
        "learn": {
            "type": "Documentation",
            "title": "Spring Microservices Resources",
            "url": "https://spring.io/microservices"
        },
        "practice": "Create two independent services communicating through REST.",
        "project": "Build a simple Order + Product microservice system."
    },

    "Docker": {
        "group": "DevOps",
        "priority": 6,
        "learn": {
            "type": "Documentation",
            "title": "Docker Get Started",
            "url": "https://docs.docker.com/get-started/"
        },
        "practice": "Create a Dockerfile and run a Java application inside a container.",
        "project": "Dockerize a Spring Boot REST API."
    },

    "AWS": {
        "group": "Cloud",
        "priority": 7,
        "learn": {
            "type": "Documentation",
            "title": "AWS Getting Started",
            "url": "https://aws.amazon.com/getting-started/"
        },
        "practice": "Learn basic cloud concepts, compute, storage and databases.",
        "project": "Deploy a simple backend application to AWS."
    },

    "Agile": {
        "group": "Software Development",
        "priority": 7,
        "learn": {
            "type": "Guide",
            "title": "Agile Guide",
            "url": "https://www.atlassian.com/agile"
        },
        "practice": "Practice Scrum concepts, sprints, backlog and standups.",
        "project": "Manage a small software project using a Scrum board."
    }
}


def get_learning_resource(skill):
    """
    Returns learning information for one skill.
    """

    resource = RESOURCE_MAP.get(skill)

    if resource:
        return {
            "skill": skill,
            "status": "Available",
            **resource
        }

    return {
        "skill": skill,
        "status": "Resource not configured",
        "group": "Other",
        "priority": 99,
        "learn": None,
        "practice": "Find a verified learning resource.",
        "project": "Create a small project using this skill."
    }


def build_learning_plan(skill_gap_result):
    """
    Converts Skill Gap Analyzer output into a learning plan.
    """

    if not skill_gap_result:
        return {
            "status": "ERROR",
            "message": "Skill gap result is empty"
        }

    if skill_gap_result.get("status") != "OK":
        return {
            "status": "ERROR",
            "message": "Invalid skill gap result"
        }

    gaps = skill_gap_result.get("skill_gaps", [])

    plan = []

    for gap in gaps:

        skill = gap.get("skill")

        resource = get_learning_resource(skill)

        plan.append({
            "skill": skill,
            "status": gap.get("status"),
            "priority": gap.get("priority"),
            "type": gap.get("type"),
            "reason": gap.get("reason"),

            "learning": {
                "group": resource.get("group"),
                "resource": resource.get("learn"),
                "practice": resource.get("practice"),
                "mini_project": resource.get("project")
            }
        })

    # Sort High before Medium and then by configured priority
    priority_order = {
        "High": 1,
        "Medium": 2,
        "Low": 3
    }

    plan.sort(
        key=lambda x: (
            priority_order.get(x["priority"], 99),
            RESOURCE_MAP.get(x["skill"], {}).get("priority", 99)
        )
    )

    return {
        "status": "OK",

        "student": skill_gap_result.get("student"),

        "job": skill_gap_result.get("job"),

        "summary": {
            "total_learning_items": len(plan),
            "high_priority": sum(
                1 for item in plan
                if item["priority"] == "High"
            ),
            "medium_priority": sum(
                1 for item in plan
                if item["priority"] == "Medium"
            )
        },

        "learning_plan": plan
    }


if __name__ == "__main__":

    # Test input from Skill Gap Analyzer

    skill_gap_result = {
        "status": "OK",

        "student": "Gautam Singh",

        "job": {
            "title": "Java Developer Intern",
            "company": "Harsham Group"
        },

        "skill_gaps": [
            {
                "skill": "Spring Boot",
                "status": "Missing",
                "priority": "High",
                "type": "Required",
                "reason": "Required by the job description"
            },
            {
                "skill": "Spring MVC",
                "status": "Missing",
                "priority": "High",
                "type": "Required",
                "reason": "Required by the job description"
            },
            {
                "skill": "Hibernate",
                "status": "Missing",
                "priority": "High",
                "type": "Required",
                "reason": "Required by the job description"
            },
            {
                "skill": "JPA",
                "status": "Missing",
                "priority": "High",
                "type": "Required",
                "reason": "Required by the job description"
            },
            {
                "skill": "JUnit",
                "status": "Missing",
                "priority": "High",
                "type": "Required",
                "reason": "Required by the job description"
            },
            {
                "skill": "REST APIs",
                "status": "Missing",
                "priority": "Medium",
                "type": "Preferred",
                "reason": "Listed as preferred / good to have"
            },
            {
                "skill": "Docker",
                "status": "Missing",
                "priority": "Medium",
                "type": "Preferred",
                "reason": "Listed as preferred / good to have"
            }
        ]
    }

    result = build_learning_plan(skill_gap_result)

    print(json.dumps(result, indent=2))