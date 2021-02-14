FROM quay.io/operator-framework/ansible-operator:v1.4.0

COPY requirements.txt ${HOME}/requirements.txt

USER root

RUN pip3 install -r ${HOME}/requirements.txt

COPY requirements.yml ${HOME}/requirements.yml
RUN ansible-galaxy collection install -r ${HOME}/requirements.yml \
 && chmod -R ug+rwx ${HOME}/.ansible

COPY watches.yaml ${HOME}/watches.yaml
COPY roles/ ${HOME}/roles/
COPY playbooks/ ${HOME}/playbooks/
