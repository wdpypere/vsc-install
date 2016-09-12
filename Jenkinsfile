node {
  stage 'checkout git'
  checkout scm
  stage 'test'
  sh "python setup.py test || true"
  stage 'mailing results'
  emailext attachLog: true, body: 'See ${env.BUILD_URL}', recipientProviders: [[$class: 'CulpritsRecipientProvider']], subject: '"Jenkins Test has finished with ${currentBuild.result}"'
}
