Frontend:
    - Ask user for transcript and store in a S3 bucket
    - ask user for PC
Backend:
    - python script grab pdf from S3, read it and access all the data we need (Most recent quarter, Quarter GPA, overall GPA, graded credits)
    - store this information in a database to be easily accessed by owner in a JSON, split by PC