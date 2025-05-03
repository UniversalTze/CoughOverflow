import boto3
import celery
import fastapi

def main():
    # Check installed version
    print(boto3.__version__)
    print(celery.__version__)
    print(fastapi.__version__)

    print("Hello from work.py inside the Docker container!")

if __name__ == "__main__":
    main()