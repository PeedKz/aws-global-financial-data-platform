# 🌍 AWS Global Financial Data Platform

End-to-end data engineering project that simulates a real-world financial data platform using AWS.

This project demonstrates how to design, build, and orchestrate a scalable data platform capable of ingesting, processing, and serving financial data for analytics and business intelligence.

## 🚀 Key Features

- Data ingestion from external financial APIs (Python)
- Scalable data lake architecture on AWS S3 (Bronze layer)
- Distributed data processing using PySpark (AWS Glue / EMR)
- Lakehouse architecture with Iceberg/Parquet tables
- Data quality validation and monitoring
- Data warehouse modeling for analytics consumption
- Infrastructure as Code using Terraform
- Workflow orchestration and automation

## 🧱 Architecture Overview

Data Sources  
→ API Ingestion (Python)  
→ AWS S3 (Data Lake - Bronze)  
→ PySpark Processing (Glue / EMR)  
→ Lakehouse Tables (Iceberg / Parquet)  
→ Data Warehouse Layer  
→ Analytics / BI  

## 🛠️ Tech Stack

- AWS (S3, Glue, EMR, Athena)
- PySpark
- Terraform (Infrastructure as Code)
- Python
- SQL
- Iceberg / Parquet
- Data Quality (Glue Data Quality / Custom Rules)

## 🎯 Purpose

This project was built to replicate real-world data engineering challenges, focusing on scalability, data quality, and modern lakehouse architecture — aligned with global data engineering standards.

## 📈 What this project demonstrates

- Production-like data pipeline design
- Cloud-native data engineering (AWS)
- Data modeling and transformation at scale
- Data quality and governance practices
- End-to-end ownership of a data platform
