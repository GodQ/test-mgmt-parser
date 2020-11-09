cp test-mgmt-*.service /etc/systemd/system

systemctl enable test-mgmt-parser.service

systemctl start test-mgmt-parser.service

