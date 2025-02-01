# About this Project: Price Collection - Group 11. 
The aim of the project is to create a price reporting tool in Python.
Data source: idealo.de. ebay.de and amazon.de html web pages with price listing for particular products. Products and their URLs are defined beforehand.
Data is analyzed and visualized to show change of the prices over the time and compare it to the price of our G7 company.

## Key Components
The project consists of following components that are developed by 4 team members that will send an automatic email to customers (predefined address) if the rank of our price for some product(s) changes.
- idealo.py
- ebay_amazon_collection.py
- products.db
- visualization.py
- rank_email.py
- main.py
- requirements.txt
- readme.md
- .env

## Prerequisites  
Before running this project, ensure you have the following:  

### **System Requirements**  
- OS: Debian 12 (Bookworm)
- Python 3.x
- MySQL (MariaDB)
- Git
- PHPMyAdmin (for database management)
- webhook (for handling web callbacks)

## Key Features
- Data Collection:
  - Collects product data from Idealo, eBay and Amazon
- Data Storage:
  - Stores scraped data in MySQL database
- Data Analysis:
  - Generates graphics for price comparison
- Alert Mechanism:
  - Sends an email if our company price rank chanegs
- Deployment:
  - The project is deployed on an AWS EC2 instance for cloud-based execution
- Error Handling & Logging:
  - Logs collection status and captures errors for debugging

## Project Structures 

```price_collections/
├── main.py                # Entry point for the application
├── data/                  # Collected data storage
├── logs/                  # Log files for data collection activities
├── requirements.txt       # Project dependencies
├── .env.template          # Environment variable template file
└── README.md              # Project documentation
```

## Authors:
- RUMMAN ZAMAN - [GitHub Profile](https://github.com/rummanz)
- UDVAL OYUNSAIKHAN - [GitHub Profile](https://github.com/UdvalO)
- DUSHAN WANIGASINGHE - [GitHub Profile](https://github.com/dushan0203)
- ASINI WANNIARACHCHI - [GitHub Profile](https://github.com/AsiniW14)

## Additional
The project is deployed on AWS and the environment can be replacted by following steps:

### **Step 1: Launch an EC2 Instance**  
1. Go to the [AWS EC2 Dashboard](https://aws.amazon.com/ec2/) and create a new instance.  
2. Select **Ubuntu 20.04 LTS** as the operating system.  
3. Choose the instance type (`t2.micro` for testing).  
4. Configure security groups to allow access via SSH (port 22) and any additional ports needed (like 5000 for web applications).  

### **Step 2: Connect to the Instance**  
After launching the instance, connect to it using SSH:  
```bash
ssh -i "your-key.pem" ec2-user@your-ec2-public-ip
```
### **Step 3: Install Dependencies**
```
sudo apt update
sudo apt install git mariadb-server phpmyadmin python3-pip webhook
```

### **Step 4: Clone the Repository**
```
git clone https://github.com/rummanz/price-collection
cd price-collection
```

### **Step 5: Install Project Dependencies**
```
pip3 install -r requirements.txt
```

### **Step 6: Start the application**
```
python3 main.py
```

