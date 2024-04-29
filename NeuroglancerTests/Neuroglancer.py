import neuroglancer

ip = '0.0.0.0' # or public IP of the machine for sharable display
port = 8080 # change to an unused port number
neuroglancer.set_server_bind_address(bind_address=ip, bind_port=port)

viewer = neuroglancer.Viewer()

with viewer.txn() as s:
    s.layers['image'] = neuroglancer.ImageLayer(source='precomputed://http://braingenix.org:8000/NeuroglancerDataset')
    # s.layers['segmentation'] = neuroglancer.SegmentationLayer(source='precomputed://gs://neuroglancer-janelia-flyem-hemibrain/v1.0/segmentation', selected_alpha=0.3)

print(viewer)


while True:
    pass
