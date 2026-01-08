metadata = dict(
    name='Demo passed Test1',
    ID='CASE-003',
    creator='tengkang.teng@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='ModelLoader', uri='oss://bucket/resnet50.onnx'),
    dict(type='dummy.Compiler', 
         dump_IR={
             'need_dump': True,
             'pass': ['FusePadConv', 'FuseConvConv']
         }),
    dict(type='dummy.Runner'),
    dict(type='NumericsComparator', rtol=1e-3),
    dict(type='ConsoleCollector'),
    dict(type='JsonResultCollector', output_file='pass_case_1_result.json')
]

precision = 'fp32'
