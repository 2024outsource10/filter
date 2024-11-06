FROM python:3.10-alpine
COPY . /root
WORKDIR /root
RUN pip3 install --break-system-packages -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
EXPOSE 3005
ENTRYPOINT ["python","/root/server.py"]
