metadata = dict(
    name='Demo failed Test',
    ID='CASE-002',
    creator='tengkang.tk@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='demo.ModelLoader', uri='oss://bucket/vgg16.onnx'),
    dict(type='demo.DummyCompiler'),

    # 故意跳过 Runner 步骤，导致没有输出结果
    # dict(type='demo.DummyRunner'),

    # NumericsComparator 将因为找不到 output_tensor 而抛出异常 -> FAIL
    dict(type='demo.NumericsComparator', rtol=1e-3),

    dict(type='demo.ConsoleCollector'),
    dict(type='demo.JsonResultCollector', output_file='fail_case_1_result.json')
]

precision = 'int8'
