from dataclasses import dataclass, field
import time
import easysnmp
import os

@dataclass
class Test:
    '''refers to data of test class'''
    oid: str = field(default='', init=True)
    # command can be READONLY/SETTABLE (get/set)
    mib_type: str = field(default='', init=True)
    mib_value: int = field(default='', init=True)

@dataclass
class SnmpConfiguration:
    '''object for easy and readable snmp configuration'''
    version: int = field(init=True)
    community: str = field(init=True)
    host: str = field(init=True)
    port: int = field(init=True)


def snmp_set(snmp_conf: SnmpConfiguration, test: Test) -> None:
    mib_object = easysnmp.snmp_set(test.oid, test.mib_value, test.mib_type, hostname = snmp_conf.host, version = snmp_conf.version)

def snmp_get(snmp_conf: SnmpConfiguration, test: Test):
    try:
        auth_pass = os.getenv('AUTH_PASS')
        priv_pass = os.getenv('PRIV_PASS')
        user_name = os.getenv('USER_NAME')
        print(f'auth_pass: {auth_pass}, priv_pass: {priv_pass}, user_name: {user_name}')
        #session = easysnmp.Session(hostname=snmp_conf.host, remote_port=snmp_conf.port,community=snmp_conf.community, version=2)
        #host = snmp_conf.host + ':' + str(snmp_conf.port)
        #mib_objects = easysnmp.snmp_get(test.oid, hostname = snmp_conf.host, version = snmp_conf.version)
        mib_object = easysnmp.snmp_get(test.oid, hostname=snmp_conf.host, version=snmp_conf.version, 
                  security_level = 'auth_with_privacy', security_username = user_name, 
                  privacy_protocol = 'AES', privacy_password = priv_pass,
                  auth_protocol = 'SHA', auth_password = auth_pass)
        #mib_objects = session.get('.1.3.6.1.2.1.1.1.0')
        print(f'mib value - {mib_object.value}')
    except Exception as e:
        print(f'{e}')
    #return mib_object.value

def loop_func():
    while True:
        time.sleep(4)

def main():
    #loop_func()
    auth_path = os.getenv('AUTH_PASS')
    print(f'blabla: {auth_path}')
    snmp_conf = SnmpConfiguration(version=3, community='public', host='snmpd:1662', port=1662)
    #test = Test(oid='1.3', mib_type='i',mib_value=15 )
    test = Test(oid='1.3.6.1.4.1.8073.1.1.4.0', mib_type='i',mib_value=15)
    #send_snmpset(snmp_conf=snmp_conf, test=test)
    #print(snmp_get(snmp_conf=snmp_conf, test=test))
    snmp_get(snmp_conf=snmp_conf, test=test)

if __name__ == '__main__':
    main()