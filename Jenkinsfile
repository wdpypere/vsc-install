// Jenkinsfile: scripted Jenkins pipefile
// [revision: Jenkinsfile@20191122-02]
// This file was automatically generated using 'python -m vsc.install.ci -f'
// DO NOT EDIT MANUALLY

node {
    stage 'checkout git'
    checkout scm
    stage 'test'
    sh 'python2.7 -V'
    sh 'python -m easy_install -U --user tox'
    sh 'tox -v'
}