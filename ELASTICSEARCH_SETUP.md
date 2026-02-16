# Elasticsearch Advanced Search - Setup Guide

**Date:** February 16, 2026
**Status:** 🟡 Infrastructure Ready - Needs Configuration

---

## Overview

HR-Plus has a comprehensive Elasticsearch-based candidate search system that provides:
- **Semantic search** across multiple fields
- **Fuzzy matching** for typo tolerance
- **Advanced filtering** (skills, location, experience, salary)
- **Relevance scoring** with field boosting
- **Database fallback** for reliability

---

## Current Status

### ✅ Implemented
- Elasticsearch document mapping ([documents.py](backend/apps/accounts/documents.py))
- Search service with filters ([search.py](backend/apps/accounts/search.py))
- Custom analyzer (lowercase, asciifolding, stemming)
- Database fallback mechanism
- API endpoint integration

### 🔴 Needs Setup
- [ ] Elasticsearch server installation/configuration
- [ ] Index creation and population
- [ ] Testing with real data
- [ ] Performance optimization
- [ ] Monitoring setup

---

## Architecture

### Document Structure

```python
CandidateDocument fields:
├── user_id (keyword)
├── email (text)
├── first_name (text)
├── last_name (text)
├── full_name (text) - BOOSTED 3x
├── phone (text)
├── location_city (text)
├── location_country (keyword)
├── work_authorization (keyword)
├── resume_parsed (object)
├── skills (text) - BOOSTED 2x
├── experience_years (integer)
├── linkedin_url (keyword)
├── portfolio_url (keyword)
├── preferred_salary_min (integer)
├── preferred_salary_max (integer)
├── source (keyword)
└── profile_completeness (integer)
```

### Search Features

**1. Full-Text Search**
```python
MultiMatch query across:
- full_name (boost: 3x) - Name matches rank highest
- email (boost: 2x)
- skills (boost: 2x)
- resume_parsed.summary
- location_city

Fuzziness: AUTO (typo tolerance)
Operator: OR (match any term)
```

**2. Filters**
- Skills: Match any of specified skills
- Location: City and country filtering
- Experience: Min/max years range
- Work Authorization: Exact match
- Source: Candidate source filtering
- Salary: Maximum salary preference

**3. Relevance Scoring**
- Name matches score highest (3x boost)
- Email and skills matches score high (2x boost)
- Other fields contribute to score
- Results ordered by relevance

---

## Installation & Setup

### 1. Install Elasticsearch

#### macOS (Homebrew)
```bash
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full

# Start Elasticsearch
brew services start elasticsearch-full

# Verify it's running
curl http://localhost:9200
```

#### Docker
```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0

# Verify
curl http://localhost:9200
```

#### Ubuntu/Debian
```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

sudo apt-get update && sudo apt-get install elasticsearch

# Start service
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

### 2. Configure Django Settings

**File:** `backend/config/settings/base.py`

```python
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200'),
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True,
    },
}

# Auto-sync: Update ES on model save
ELASTICSEARCH_DSL_AUTOSYNC = True  # Development
# ELASTICSEARCH_DSL_AUTOSYNC = False  # Production (use Celery)

# Auto-refresh after indexing
ELASTICSEARCH_DSL_AUTO_REFRESH = True  # Development
# ELASTICSEARCH_DSL_AUTO_REFRESH = False  # Production
```

**Environment Variables:**
```bash
# .env
ELASTICSEARCH_URL=http://localhost:9200

# Production
ELASTICSEARCH_URL=https://elasticsearch.production.com:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-password
```

### 3. Create and Populate Index

```bash
cd backend

# Create the index with mappings
python manage.py search_index --create

# Populate with existing data
python manage.py search_index --populate

# OR: Rebuild (delete + create + populate)
python manage.py search_index --rebuild -f

# For specific model only
python manage.py search_index --models accounts.CandidateProfile --rebuild -f
```

### 4. Verify Index

```bash
# Check index exists
curl http://localhost:9200/_cat/indices?v

# Check document count
curl http://localhost:9200/candidates/_count

# View index mapping
curl http://localhost:9200/candidates/_mapping?pretty

# Sample search
curl -X GET "http://localhost:9200/candidates/_search?pretty" -H 'Content-Type: application/json' -d'{
  "query": {
    "multi_match": {
      "query": "python django",
      "fields": ["full_name^3", "skills^2", "email^2"]
    }
  }
}'
```

---

## Usage Examples

### Backend Search Service

```python
from apps.accounts.search import CandidateSearchService

# Basic search
candidates = CandidateSearchService.search(
    query="python developer",
    limit=20
)

# Search with filters
candidates = CandidateSearchService.search(
    query="senior engineer",
    skills=["Python", "Django", "React"],
    location_city="San Francisco",
    location_country="USA",
    experience_min=5,
    experience_max=10,
    work_authorization="citizen",
    salary_max=150000,
    limit=50
)

# Results are ordered by relevance
for candidate in candidates:
    print(f"{candidate.user.get_full_name()} - {candidate.location_city}")
```

### API Endpoint

```bash
# Search candidates
curl -X GET "http://localhost:8000/api/v1/candidates/search/" \
  -H "Authorization: Bearer $TOKEN" \
  -G \
  --data-urlencode "q=python django" \
  --data-urlencode "skills=Python,Django,PostgreSQL" \
  --data-urlencode "location_city=San Francisco" \
  --data-urlencode "experience_min=3" \
  --data-urlencode "limit=20"
```

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": "uuid",
      "user": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
      },
      "location_city": "San Francisco",
      "location_country": "USA",
      "resume_parsed": {
        "skills": ["Python", "Django", "PostgreSQL", "React"],
        "summary": "Senior Software Engineer..."
      },
      "profile_completeness": 95
    }
  ]
}
```

---

## Testing

### Test Script

```python
# backend/test_elasticsearch.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.search import CandidateSearchService

# Test 1: Basic search
print("Test 1: Basic search for 'python'")
results = CandidateSearchService.search(query="python", limit=5)
print(f"Found {len(results)} candidates")
for candidate in results:
    print(f"  - {candidate.user.get_full_name()}")

# Test 2: Skills filter
print("\nTest 2: Search with skills filter")
results = CandidateSearchService.search(
    skills=["Python", "Django"],
    limit=5
)
print(f"Found {len(results)} candidates with Python and Django")

# Test 3: Location filter
print("\nTest 3: Location-based search")
results = CandidateSearchService.search(
    location_city="San Francisco",
    limit=5
)
print(f"Found {len(results)} candidates in San Francisco")

# Test 4: Fuzzy search (typos)
print("\nTest 4: Fuzzy search with typo")
results = CandidateSearchService.search(query="pyhton", limit=5)  # Typo: pyhton
print(f"Found {len(results)} candidates (typo corrected)")

print("\n✅ All tests completed!")
```

Run tests:
```bash
cd backend
python test_elasticsearch.py
```

---

## Performance Optimization

### 1. Index Settings

```python
# In documents.py
class Index:
    name = 'candidates'
    settings = {
        'number_of_shards': 3,  # Increase for large datasets
        'number_of_replicas': 1,  # For redundancy
        'refresh_interval': '30s',  # Reduce for better write performance
        'max_result_window': 10000,  # Default pagination limit
    }
```

### 2. Async Indexing with Celery

```python
# backend/apps/accounts/tasks.py
from celery import shared_task
from django_elasticsearch_dsl.registries import registry

@shared_task
def update_candidate_index(candidate_id):
    """Update single candidate in Elasticsearch."""
    from .models import CandidateProfile

    try:
        candidate = CandidateProfile.objects.get(id=candidate_id)
        registry.update(candidate)
    except CandidateProfile.DoesNotExist:
        pass

@shared_task
def bulk_update_candidates():
    """Bulk update all candidates (run periodically)."""
    from .documents import CandidateDocument
    CandidateDocument().update(CandidateProfile.objects.all())
```

Trigger async update:
```python
# In signals or views
from .tasks import update_candidate_index

# After candidate update
update_candidate_index.delay(candidate.id)
```

### 3. Query Optimization

```python
# Use source filtering to reduce payload
search = CandidateDocument.search().source(['id', 'full_name', 'email'])

# Use pagination properly
search = search[0:20]  # First 20 results

# Use aggregations for facets
search.aggs.bucket('skills', 'terms', field='skills', size=50)
search.aggs.bucket('locations', 'terms', field='location_city', size=20)
```

---

## Advanced Features

### 1. Aggregations (Faceted Search)

```python
def search_with_facets(query: str):
    """Search with aggregations for filtering UI."""
    search = CandidateDocument.search()

    if query:
        search = search.query('multi_match', query=query, fields=['full_name', 'skills'])

    # Add aggregations
    search.aggs.bucket('top_skills', 'terms', field='skills.keyword', size=20)
    search.aggs.bucket('locations', 'terms', field='location_city.keyword', size=15)
    search.aggs.bucket('sources', 'terms', field='source', size=10)
    search.aggs.bucket('experience_range', 'range', field='experience_years',
                      ranges=[
                          {'key': '0-2 years', 'to': 2},
                          {'key': '3-5 years', 'from': 3, 'to': 5},
                          {'key': '6-10 years', 'from': 6, 'to': 10},
                          {'key': '10+ years', 'from': 10},
                      ])

    response = search.execute()

    return {
        'results': [hit.to_dict() for hit in response],
        'facets': {
            'skills': [(bucket.key, bucket.doc_count) for bucket in response.aggregations.top_skills.buckets],
            'locations': [(bucket.key, bucket.doc_count) for bucket in response.aggregations.locations.buckets],
            'sources': [(bucket.key, bucket.doc_count) for bucket in response.aggregations.sources.buckets],
            'experience': [(bucket.key, bucket.doc_count) for bucket in response.aggregations.experience_range.buckets],
        }
    }
```

### 2. Highlighting

```python
search = search.highlight('full_name', 'skills', 'resume_parsed.summary',
                         pre_tags=['<mark>'], post_tags=['</mark>'])

for hit in response:
    if hasattr(hit.meta, 'highlight'):
        highlighted_skills = hit.meta.highlight.skills[0]
```

### 3. Suggestions (Did You Mean?)

```python
search = search.suggest('name_suggestion', 'pythob', term={'field': 'skills'})

response = search.execute()
suggestions = response.suggest.name_suggestion[0].options
```

### 4. Boolean Search

```python
# Must have Python AND Django
search = search.query('bool', must=[
    Q('match', skills='Python'),
    Q('match', skills='Django'),
])

# Should have React OR Vue (not required)
search = search.query('bool', should=[
    Q('match', skills='React'),
    Q('match', skills='Vue'),
])

# Must NOT have Java
search = search.query('bool', must_not=[
    Q('match', skills='Java'),
])
```

---

## Monitoring & Maintenance

### Health Check

```bash
# Cluster health
curl http://localhost:9200/_cluster/health?pretty

# Index stats
curl http://localhost:9200/_cat/indices/candidates?v&s=docs.count:desc

# Node stats
curl http://localhost:9200/_nodes/stats?pretty
```

### Reindexing

```bash
# Full reindex (downtime)
python manage.py search_index --rebuild -f

# Zero-downtime reindex (use aliases)
python manage.py search_index --use-alias --rebuild -f
```

### Backup & Restore

```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'{
  "type": "fs",
  "settings": {
    "location": "/var/backups/elasticsearch"
  }
}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"

# Restore
curl -X POST "http://localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

---

## Production Deployment

### 1. Elasticsearch Cluster Setup

**Recommended: Elastic Cloud (managed service)**
```bash
# Sign up at https://cloud.elastic.co/
# Get cloud ID and API key

# Update settings
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ['https://your-deployment.es.us-east-1.aws.elastic.cloud:9243'],
        'http_auth': ('elastic', 'your-password'),
        'use_ssl': True,
        'verify_certs': True,
    },
}
```

**Self-hosted cluster:**
- Minimum 3 nodes for high availability
- Configure data/master/ingest nodes
- Set up monitoring with Kibana
- Enable security (X-Pack)
- Configure backup strategy

### 2. Security

```python
# Enable authentication
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': [os.environ.get('ELASTICSEARCH_URL')],
        'http_auth': (
            os.environ.get('ELASTICSEARCH_USERNAME'),
            os.environ.get('ELASTICSEARCH_PASSWORD')
        ),
        'use_ssl': True,
        'verify_certs': True,
        'ca_certs': '/path/to/ca.crt',
    },
}
```

### 3. Performance Tuning

```python
# Production settings
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': [...],
        'timeout': 60,
        'max_retries': 5,
        'retry_on_timeout': True,
        'max_connections': 20,
        'connection_class': 'Urllib3HttpConnection',
    },
}

# Disable auto-sync in production
ELASTICSEARCH_DSL_AUTOSYNC = False

# Use Celery for indexing
# Schedule bulk updates every hour
CELERY_BEAT_SCHEDULE = {
    'update-elasticsearch-index': {
        'task': 'apps.accounts.tasks.bulk_update_candidates',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

---

## Troubleshooting

### Issue 1: Connection Refused
```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Check logs
tail -f /usr/share/elasticsearch/logs/elasticsearch.log

# Restart service
brew services restart elasticsearch-full  # macOS
sudo systemctl restart elasticsearch     # Linux
```

### Issue 2: Index Not Created
```bash
# Check Django settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.ELASTICSEARCH_DSL)

# Manually create index
python manage.py search_index --create -f
```

### Issue 3: Search Returns Empty
```bash
# Check document count
curl http://localhost:9200/candidates/_count

# If zero, populate index
python manage.py search_index --populate

# Check for errors
python manage.py search_index --populate --verbosity=2
```

### Issue 4: Slow Queries
```bash
# Enable slow query log
curl -X PUT "http://localhost:9200/candidates/_settings" -H 'Content-Type: application/json' -d'{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s"
}'

# View slow log
tail -f /var/log/elasticsearch/elasticsearch_index_search_slowlog.log
```

---

## Next Steps

1. **Install Elasticsearch** (see Installation section)
2. **Create index:** `python manage.py search_index --rebuild -f`
3. **Test search:** Run `test_elasticsearch.py`
4. **Frontend integration:** Update candidate search UI to use enhanced search
5. **Add facets:** Implement aggregations for filter UI
6. **Monitoring:** Set up Kibana for index monitoring

---

## Summary

The Elasticsearch infrastructure is **ready to deploy** with:
- ✅ Document mapping configured
- ✅ Search service implemented
- ✅ Advanced features (fuzzy, filters, boosting)
- ✅ Database fallback for reliability
- ✅ API endpoint ready

**Just needs:**
- 🔴 Elasticsearch server setup
- 🔴 Index population
- 🔴 Testing with real data

---

**Files:**
- `backend/apps/accounts/documents.py` - Elasticsearch document mapping
- `backend/apps/accounts/search.py` - Search service
- `backend/config/settings/base.py` - Elasticsearch configuration
- `ELASTICSEARCH_SETUP.md` - This guide
