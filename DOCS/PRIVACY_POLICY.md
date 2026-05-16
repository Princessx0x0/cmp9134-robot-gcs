# Privacy Policy — CMP9134 Robot GCS

## What PII is collected and why
This system collects and stores the following Personally Identifiable Information: usernames, bcrypt-hashed passwords, and timestamped records of every command issued to the robot. This data is collected solely to satisfy the safety audit requirement of the Ground Control Station — every action must be attributable to a named user for incident investigation purposes. No real names, email addresses, or payment information are collected.

## How long is it retained
Currently, the system retains audit logs indefinitely due to the lack of an automated deletion policy. In a real-world production environment, a 90-day retention schedule would be applied using an automated deletion script. This 90-day window follows standard industry security baselines. It fulfills the Storage Limitation principle of UK GDPR Article 5(1)(e) by ensuring that user log data is purged as soon as it is no longer required for active security monitoring.

## How is it secured
Access to the audit log is restricted via Role-Based Access Control. Only authenticated users with the Commander or Auditor role may view logs. Passwords are never stored in plaintext — bcrypt hashing with a salt factor of 12 is applied at registration. All API endpoints require a valid JWT token. The database file is not exposed outside the Docker network.