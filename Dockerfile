FROM quay.io/operator-framework/ansible-operator:v1.4.0

COPY requirements.txt ${HOME}/requirements.txt

USER root

RUN pip3 install -r ${HOME}/requirements.txt

USER 1001    

#COPY requirements.yml ${HOME}/requirements.yml
RUN chmod -R ug+rwx ${HOME}/.ansible

COPY watches.yaml ${HOME}/watches.yaml 
COPY playbooks/ ${HOME}/playbooks/
