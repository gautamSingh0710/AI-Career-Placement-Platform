LEARNING_RESOURCES = {
    "Exception Handling": {
        "type": "official",
        "provider": "Oracle Java Documentation",
        "url": "https://docs.oracle.com/javase/tutorial/essential/exceptions/",
        "topic": "Java Exception Handling"
    },
    "Database Design": {
    "type": "official",
    "provider": "PostgreSQL",
    "url": "https://www.postgresql.org/docs/current/ddl.html",
    "topic": "PostgreSQL Data Definition / Database Design"
},

"JUnit": {
    "type": "official",
    "provider": "JUnit",
    "url": "https://docs.junit.org/current/user-guide/",
    "topic": "JUnit User Guide"
},

"Mockito": {
    "type": "official",
    "provider": "Mockito",
    "url": "https://site.mockito.org/",
    "topic": "Mockito Documentation"
},

    "Multithreading": {
        "type": "official",
        "provider": "Oracle Java Documentation",
        "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/",
        "topic": "Java Concurrency"
    },

    "Collections": {
        "type": "official",
        "provider": "Oracle Java Documentation",
        "url": "https://docs.oracle.com/javase/tutorial/collections/",
        "topic": "Java Collections Framework"
    },

    "Spring Boot": {
        "type": "official",
        "provider": "Spring",
        "url": "https://spring.io/guides",
        "topic": "Spring Boot Guides"
    },

    "Spring MVC": {
        "type": "official",
        "provider": "Spring",
        "url": "https://docs.spring.io/spring-framework/reference/web/webmvc.html",
        "topic": "Spring Web MVC"
    },

    "Hibernate": {
        "type": "official",
        "provider": "Hibernate",
        "url": "https://hibernate.org/orm/documentation/",
        "topic": "Hibernate ORM"
    },

    "JPA": {
        "type": "official",
        "provider": "Jakarta EE",
        "url": "https://jakarta.ee/specifications/persistence/",
        "topic": "Jakarta Persistence"
    },

    "SQL": {
        "type": "official",
        "provider": "PostgreSQL",
        "url": "https://www.postgresql.org/docs/current/tutorial.html",
        "topic": "SQL Tutorial"
    },

    "REST APIs": {
        "type": "official",
        "provider": "MDN",
        "url": "https://developer.mozilla.org/en-US/docs/Glossary/REST",
        "topic": "REST APIs"
    },

    "Microservices": {
        "type": "official",
        "provider": "Microsoft",
        "url": "https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices",
        "topic": "Microservices Architecture"
    },

    "Docker": {
        "type": "official",
        "provider": "Docker",
        "url": "https://docs.docker.com/get-started/",
        "topic": "Docker Getting Started"
    },

    "AWS": {
        "type": "official",
        "provider": "AWS",
        "url": "https://aws.amazon.com/getting-started/",
        "topic": "AWS Getting Started"
    }
}


def get_learning_resources(skill_gaps):
    if not isinstance(skill_gaps, list):
        return {
            "status": "ERROR",
            "message": "skill_gaps must be a list"
        }

    resources = []

    for gap in skill_gaps:
        if not isinstance(gap, dict):
            continue

        skill = gap.get("skill")
        if not skill:
            continue

        resource = LEARNING_RESOURCES.get(skill)

        if not resource:
            continue

        resources.append({
            "skill": skill,
            "priority": gap.get("priority"),
            "type": gap.get("type"),
            "resource": resource
        })

    return {
        "status": "OK",
        "total_resources": len(resources),
        "resources": resources
    }


if __name__ == "__main__":
    test_gaps = [
        {
            "skill": "Spring Boot",
            "priority": "High",
            "type": "Required"
        },
        {
            "skill": "SQL",
            "priority": "High",
            "type": "Required"
        },
        {
            "skill": "Docker",
            "priority": "Medium",
            "type": "Preferred"
        }
    ]

    import json

    print(
        json.dumps(
            get_learning_resources(test_gaps),
            indent=2
        )
    )