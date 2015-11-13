## omgbenchmark

####  Rally plugin for testing oslo.messaging


######  How to benchmark oslo.messaging with rally

- Install rally
  ```
     git clone http://github.com/openstack/rally
     cd rally
     ./install_rally_sh
  ```
   
- Install following packages:
  *oslo.messaging*
  *petname*
  *scipy*
  
- Create rally deployment:

  modify **deployment.json** corresponding your rabbitmq/0mq/.. location then run
  ```
  rally --plugin-paths <path_to_rally_plugin_files> deployment create --file=deployment.json --name=omg
  ```
  
- Run task:
  modify **task.json** with your benchmarking parameters and config opts then run
  ```
  rally --plugin-paths <path_to_rally_plugin_files> task start task.json
  ```
