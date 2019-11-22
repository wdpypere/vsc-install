// Jenkinsfile: scripted Jenkins pipefile
// [revision: Jenkinsfile@20191122-01]
// This file was automatically generated using 'python -c vsc.install.ci -f'
// DO NOT EDIT MANUALLY

node {
    stage 'checkout git'
    checkout scm
    stage 'test'
    sh 'python2.7 -V'
    sh 'tox -v'
}