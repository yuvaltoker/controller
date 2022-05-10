#ifndef SUBAGENTS_H
#define SUBAGENTS_H

/* function declaration */
void connectToRedis(void);
void shutdownRedis(void);
void init_subagents(void);
Netsnmp_Node_Handler handle_myIntMibObject;
Netsnmp_Node_Handler handle_myStringMibObject;
void GET_objects_redis(int mode);
void SET_objects_redis(int mode);
#endif /* SUBAGENTS_H */

