labels = ['demo', 'daily']

pipeline = [
    # 步骤 1: 加载模型
    dict(type='ModelLoader', uri='oss://bucket/resnet50.onnx'),
    
    # 步骤 2: 编译 (Dummy)
    dict(type='dummy.Compiler'),
    
    # 步骤 3: 推理 (Dummy)
    dict(type='dummy.Runner'),
    
    # 步骤 4: 对比结果
    dict(type='NumericsComparator', rtol=1e-3),
    
    # 步骤 5: 模拟耗时
    dict(type='SleepStep', seconds=0.5),

    # 步骤 6: 收集结果到控制台
    dict(type='ConsoleCollector'),

    # 步骤 7: 收集结果到 JSON 文件
    dict(type='JsonResultCollector', output_file='result.json')
]

# case level configs
precision = 'fp32'