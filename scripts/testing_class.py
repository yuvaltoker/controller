from dataclasses import dataclass, field
import easysnmp

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
    version: str = field(init=True)
    community: str = field(init=True)
    host: str = field(init=True)
    port: int = field(init=True)


def snmp_set(snmp_conf: SnmpConfiguration, test: Test) -> None:
        mib_object = easysnmp.snmp_set(test.oid, test.mib_value, test.mib_type, hostname = snmp_conf.host, version = snmp_conf.version)

def snmp_get(snmp_conf: SnmpConfiguration, test: Test):
        mib_object = easysnmp.snmp_get(test.oid, hostname = snmp_conf.host, version = snmp_conf.version)
        return mib_object.value

def main():
    snmp_conf = SnmpConfiguration(version='2', community='public', host='snmpd', port=1662)
    #test = Test(oid='1.3', mib_type='i',mib_value=15 )
    test = Test(oid='1.3.6.1.4.1.8072.2.4.1.1.4', mib_type='i',mib_value=15)
    #send_snmpset(snmp_conf=snmp_conf, test=test)
    print(snmp_get(snmp_conf=snmp_conf, test=test))

if __name__ == '__main__':
    main()