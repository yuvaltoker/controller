#
# Warning: you may need more libraries than are included here on the
# build line.  The agent frequently needs various libraries in order
# to compile pieces of it, but is OS dependent and we can't list all
# the combinations here.  Instead, look at the libraries that were
# used when linking the snmpd master agent and copy those to this
# file.
#

CC=gcc -std=c99
LIBS=-levent -lnetsnmp -lhiredis -lnetsnmpagent -lnetsnmpmibs -lnetsnmphelpers
NETSNMPCONFIG=net-snmp-config

NETSNMPCFLAGS := $(shell $(NETSNMPCONFIG) --base-cflags)

NETSNMPLIBS := $(shell $(NETSNMPCONFIG) --agent-libs)

LIB=$(NETSNMPLIBS)

OBJS1=snmpdemoapp.o
#OBJS2=example-daemon.o nstAgentSubagentObject.o subagents.o hiredis/hiredis.o hiredis/async.o hiredis/sds.o hiredis/net.o hiredis/read.o hiredis/alloc.o
OBJS2=example-daemon.o subagents.o hiredis/hiredis.o hiredis/async.o hiredis/sds.o hiredis/net.o hiredis/read.o hiredis/alloc.o
OBJS3=asyncapp.o
#TARGETS=example-daemon snmpdemoapp asyncapp
TARGETS=example-daemon

CFLAGS=-I. `net-snmp-config --cflags`
ANOTHERFLAG=-std=c99
BUILDLIBS=`net-snmp-config --libs `
BUILDAGENTLIBS=`net-snmp-config --agent-libs`
LIBINCLUDES= -L/create_snmpd/hiredis

# shared library flags (assumes gcc)
DLFLAGS=-fPIC -shared

all: $(TARGETS)

snmpdemoapp: $(OBJS1)
	$(CC) -o snmpdemoapp $(OBJS1) $(BUILDLIBS)

asyncapp: $(OBJS3)
	$(CC) -o asyncapp $(OBJS3) $(BUILDLIBS)

example-daemon: $(OBJS2) Makefile
	$(CC) -o example-daemon $(LIBINCLUDES) $(OBJS2) $(LIBS) $(BUILDAGENTLIBS) $(BUILDLIBS) $(LIB)

clean:
	rm $(OBJS2)

nstAgentPluginObject.so: nstAgentPluginObject.c Makefile
	$(CC) $(CFLAGS) $(DLFLAGS) -c -o nstAgentPluginObject.o nstAgentPluginObject.c
	$(CC) $(CFLAGS) $(DLFLAGS) -o nstAgentPluginObject.so nstAgentPluginObject.o

