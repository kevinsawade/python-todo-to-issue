FROM python:3
COPY main.py /main.py
COPY requirements.py /requirements.py
RUN python -m pip install --upgrade pip
RUN pip install /requirements.py
CMD ["python", "/main.py"]
