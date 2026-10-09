# Scaling

YouCademy takes the approach that engineering to scale is done as needed and
supported by evidence. We believe that pressure-testing our system to
demonstrate capacity or uncover scaling issues is the prudent way to
balance business risk and opportunity cost of premature optimizations.
(For our purposes, peak concurrency is 1000 users in locust. )

## Main App

The main application is a Django API. It is hosted in
[Google Cloud Run](https://cloud.google.com/run) to allow for dynamic
scaling of the application and cost control.

### Load Testing Results
July 30th
- Cold Start time: 10.77s -22.51 s
#### At peak concurrency 
- Request latencies: (min) 99th percentile 1.061, 95th  1.021, 50th
- Maximum concurrent requests: 739
- CPU usage 79.86%
- Memory usage: 100%
- Pricing:  $0.00001800 / vCPU-second beyond free tier, $0.00000200 / GiB-second beyond free tier. So 0.00004 per second per instance.
#### Response Times:

Median: 9,000 ms
Average: 12,240.79 ms
Min: 164.45 ms
Max: 76,791.45 ms

#### Most Common Errors
- 503 Service Unavailable
- 429 Too Many Requests
#### Most problematic endpoint
/pages/login: 1,230 failures (mostly 429 errors)
### Limitations
### Locust Charts
From 1-10 users
![total_requests_per_second_1722361146 933](https://github.com/user-attachments/assets/018727b4-cb4e-4c7d-a94a-3293e1a7c01c)

From 10-100 users 
![total_requests_per_second_1722361146 933 (1)](https://github.com/user-attachments/assets/50730042-c817-4f01-8073-f3e0250b5ccd)

From 100-1000 users
![total_requests_per_second_1722361146 933 (2)](https://github.com/user-attachments/assets/81dcb220-2936-47ef-9b28-b99e10c06b48)


The current approach has some limitations imposed by Cloud Run defaults.

* 100 [default max instances](https://cloud.google.com/run/docs/about-instance-autoscaling)
* 80 [default concurrent requests](https://cloud.google.com/run/docs/about-concurrency) per instance
* 1000 [maximum concurrent requests](https://cloud.google.com/run/docs/about-concurrency) per instance

We intend to follow the [concurrency tuning](https://cloud.google.com/run/docs/tips/general#optimize_concurrency) guidance as well as the
[Python-specific](https://cloud.google.com/run/docs/tips/python)
guidance that Google Cloud Run provides.

## Logging

We use asynchronous logging and the Google Cloud Logging service.

### Load Testing Results

N/A

### Limitations

- Ingestion is limited to 1,500 requests per minute per project by default, which can be increased to 60,000 with approval.
- Individual log entries are limited to 256 KiB in size.
- The default retention period is 30 days, which may not be sufficient for long-term analysis needs.
- Query performance can degrade for large volumes of data or long time ranges, with a 10-minute timeout.
- There's a delay of about 10 minutes for log exports via sinks.
- While log ingestion is free, storage and analysis costs can become significant at scale.
- Some advanced query features are not available for very recent logs (less than 24 hours old).

## Storage

We use the Google Cloud Storage service.

### Load Testing Results

TBD

### Limitations
- Maximum number of object list requests per bucket: 5,500 per second
- Maximum number of object get/read requests: 5,500 per second per prefix
- Maximum number of object write requests: 1,000 per second per prefix

## Relational Database

We use the Google Cloud SQL service.

### Load Testing Results

At peak concurrency: 
- 14.06 % of CPU used.
- 40.5 % of Memory Used
- 99th percentile query latency of 516.17 us (microseconds).

### Limitations

- 2vcpu, 8GB memory
- 10 GB storage
- **Replication**:
  - Maximum read replicas: Up to 10 per primary instance
  - Cross-region replication available, but with potential increased latency

- **Backups**:
  - Automated backups: Retained for 7 days by default (configurable up to 365 days)
  - Maximum backup retention period: 365 days

- **Maintenance Windows**:
  - Weekly maintenance window required, which may cause brief downtime

- **Scaling**:
  - Vertical scaling (changing machine type) requires instance restart
  - Storage can be scaled up without restart, but cannot be scaled down


## Key/Value Store

We use Mongo Atlas service.

### Load Testing Results

At peak concurrency: 
- there was a max of 70 IOPS. Well under it's upper limit of 600.
- 613 MB of memory used.


### Limitations
-RAM: 1.7 GB
-Storage:
-Initial: 10 GB
-Feature: Auto-expand storage
-IOPS: 600 IOPS (Input/Output Operations Per Second)
## In Memory Cache

We use the Google Serverless VPC Connector and Cloud Memory Store services.

### Load Testing Results

TBD

### Limitations

TBD

## Next Steps: 
- Add a cache for static pages.
- Add htmx to reduce content reloading.
- Make image leaner to reduce cold start times.
- 
