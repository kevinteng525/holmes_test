metadata = dict(
    name='Demo passed Test2',
    ID='CASE-004',
    creator='tengkang.tk@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='demo.ModelLoader', uri='oss://bucket/bert.onnx'),
    dict(type='demo.DummyCompiler',
         dump_IR={
             'need_dump': False
         }),
    dict(type='demo.DummyRunner'),
    dict(type='demo.NumericsComparator', rtol=1e-4),
    dict(type='demo.ConsoleCollector'),
    dict(type='demo.JsonResultCollector', output_file='pass_case_2_result.json')
]

precision = 'fp16'
