
labels = ['demo', 'daily']

pipeline = [
    # 步骤 1: 加载模型
    dict(type='ModelLoader', uri='oss://bucket/resnet50.onnx'),
    
    # 步骤 2: 编译 (Dummy)
    dict(type='DummyCompiler'), 
    
    # 步骤 3: 推理 (Dummy)
    dict(type='DummyRunner'),
    
    # 步骤 4: 对比结果
    dict(type='NumericsComparator', rtol=1e-3),
    
    # 步骤 5: 模拟耗时
    dict(type='SleepStep', seconds=0.5)
]

# case level configs
precision = 'fp32'
