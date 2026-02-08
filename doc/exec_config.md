## 现在需要改进一下导出case CSV的逻辑：
### Before
之前导出的时候会merge plan，suite，case各level的配置，然后导出最终merge后的config_files,env_file,setup_scripts,vm_image,docker_image等
### Now
现在我希望按最终merge好后的配置先在同一个文件夹下创建一个exec_config的文件夹，在这下面创建相应的yaml文件，里面包含了所有的配置，比如：
```yaml
environment:
  run_at: vm+docker
  base_image: base_vm_image.qcow2
  # docker_image: art.eng.t-head.cn/ptgai-docker_ai-tmp/holmes:torch2.6-cuda12.3-ubuntu22.04-py310
  docker_id: torch2.6-cuda12.3-ubuntu22.04-py310
  package: PPU_SDK_Torch_Holmes_CUDA12.9.0_Ubuntu2404_PyTorch2.9.0_py312.tar.gz

runtime:
  hw_type: ppu
  driver: umd 
  setup_driver: true
  resource:
    cpu: 8
    memory: 16
    ppu: 1
    gpu: 1
    # host: 2
  labels: OAM-810E

config_files:
  cmodel_cfg: v2/environments/holmes/configs/cmodel/dynamo.cfg
  settings_cfg: v2/environments/holmes/configs/settings/default.cfg

env_file: v2/environments/holmes/envs/dynamo.env

setup_script: v2/environments/holmes/setup_scripts/dynamo.sh
```
由于一般来说这些执行配置不会定义在case level，所以这个生成的配置可以按照suite的名字来生成，当然如果这个suite也没有定义这些字段，则不生成，默认会生成一个plan级别的执行配置文件，就命名为default.yaml

然后在导出的CSV中，去掉config_files,env_file,setup_scripts,vm_image,docker_image,global config 这几列，新增一个exec_config列，里面包含上述yaml文件的路径

最后，请在CSV中新增两列，component和domain，分别从plan和suite的metadata中获取。