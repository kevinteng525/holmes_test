请改进一下设计文档：
1. 这套测试框架需要更common一点，不一定只是为了推理引擎的自动化测试，还需要支持其他各种测试；为了支持推理引擎的测试，只需要实现相应的插件就可以了。
2. 针对每个case的不同步骤，需要可以传递context，context里可以灵活的添加各种配置，这样不同步骤的具体实现可以读取context里的配置并作相应操作，比如compile的时候命令行里加一些参数，dump前后的IR等等。
3. 在外层，还需要支持定义test suite，suite里可以包含多个case，可以根据label去选择相应的case，比如daily test，checkin test，这些label可以定义在case的config里
4. 还需要有test plan，test plan里可以包含多个suite，还有测试环境，指定用哪个dockerfile，用哪些配置（这些配置是整个test plan的层面的，所有case都用同一个配置）
5. 仓库里还需要能管理dockerfile，也就是各种不同的环境