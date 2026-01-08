metadata = dict(
    name='Demo failed Test',
    ID='CASE-002',
    creator='tengkang.teng@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='ModelLoader', uri='oss://bucket/vgg16.onnx'),
    dict(type='dummy.Compiler'),
    
    # 故意跳过 Runner 步骤，导致没有输出结果
    # dict(type='dummy.Runner'),
    
    # NumericsComparator 将因为找不到 output_tensor 而抛出异常 -> FAIL
    dict(type='NumericsComparator', rtol=1e-3),
    
    dict(type='ConsoleCollector'),
    dict(type='JsonResultCollector', output_file='fail_case_1_result.json')
]

precision = 'int8'
