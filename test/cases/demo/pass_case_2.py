metadata = dict(
    name='Demo passed Test2',
    ID='CASE-004',
    creator='tengkang.teng@alibaba-inc.com'
)
labels = ['report_demo']

pipeline = [
    dict(type='ModelLoader', uri='oss://bucket/bert.onnx'),
    dict(type='dummy.Compiler', 
         dump_IR={
             'need_dump': False
         }),
    dict(type='dummy.Runner'),
    dict(type='NumericsComparator', rtol=1e-4),
    dict(type='ConsoleCollector'),
    dict(type='JsonResultCollector', output_file='pass_case_2_result.json')
]

precision = 'fp16'
