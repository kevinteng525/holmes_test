metadata = dict(
    name='Demo ResNet50 Test',
    ID='CASE-001',
    creator='tengkang.tk@alibaba-inc.com'
)
labels = ['demo', 'daily']

pipeline = [
    # 步骤 1: 加载模型
    dict(type='demo.ModelLoader', uri='oss://bucket/resnet50.onnx'),

    # 步骤 2: 编译 (Dummy)
    dict(type='demo.DummyCompiler',
         dump_IR={
             'need_dump':True,
             'pass': ['FusePadConv', 'FuseConvConv']
         }),

    # 步骤 3: 推理 (Dummy)
    dict(type='demo.DummyRunner'),

    # 步骤 4: 对比结果
    dict(type='demo.NumericsComparator', rtol=1e-3),

    # 步骤 5: 模拟耗时
    dict(type='demo.SleepStep', seconds=0.5),

    # 步骤 6: 收集结果到控制台
    dict(type='demo.ConsoleCollector'),

    # 步骤 7: 收集结果到 JSON 文件
    dict(type='demo.JsonResultCollector', output_file='result.json')
]

# case level configs
precision = 'fp32'