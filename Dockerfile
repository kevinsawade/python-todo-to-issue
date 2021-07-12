FROM python:3
COPY main.py /main.py
COPY requirements.txt /requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install /requirements.txt
CMD ["python", "/main.py"]
