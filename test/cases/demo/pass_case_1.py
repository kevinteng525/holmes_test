metadata = dict(
    name='Demo passed Test1',
    ID='CASE-003',
    creator='tengkang.teng@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='demo.ModelLoader', uri='oss://bucket/resnet50.onnx'),
    dict(type='demo.DummyCompiler',
         dump_IR={
             'need_dump': True,
             'pass': ['FusePadConv', 'FuseConvConv']
         }),
    dict(type='demo.DummyRunner'),
    dict(type='demo.NumericsComparator', rtol=1e-3),
    dict(type='demo.ConsoleCollector'),
    dict(type='demo.JsonResultCollector', output_file='pass_case_1_result.json')
]

precision = 'fp32'
