from bs4 import BeautifulSoup


# 理论课参数
def get_params(html, course, content):
    soup = BeautifulSoup(html, "html.parser")
    pj_panel_body = soup.find(attrs={'class': 'panel-body xspj-body'})
    pj_dxs = pj_panel_body.find_all(attrs={'class': 'panel panel-default panel-pjdx'})
    data = {
        'ztpjbl': pj_panel_body['data-ztpjbl'],
        'jszdpjbl': pj_panel_body['data-jszdpjbl'],
        'xykzpjbl': pj_panel_body['data-xykzpjbl'],
        'jxb_id': course['jxb_id'],
        'kch_id': course['kch_id'],
        'jgh_id': course['jgh_id'],
        'xsdm': course['xsdm'],
        # 评价提交状态参数，取值含义：已评价并保存过当前课程：0，已提交评价：1，未评价：-1
        'tjzt': course['tjzt'],
    }
    # 评价对象
    for i, pj_dx in enumerate(pj_dxs):
        data['modelList[%s].pjmbmcb_id' % i] = pj_dx['data-pjmbmcb_id']
        data['modelList[%s].pjdxdm' % i] = pj_dx['data-pjdxdm']
        data['modelList[%s].fxzgf' % i] = ''
        data['modelList[%s].py' % i] = content
        data['modelList[%s].xspfb_id' % i] = pj_dx['data-xspfb_id']
        # 评价状态参数，取值含义：已评价并保存（已评完）：1，未评完/未评价：0。
        # 所以如果需要在评价完成后将当前课程评价状态设置为已评完，则需要将该值设置为1，设置为0则会显示为未评完状态
        data['modelList[%s].pjzt' % i] = 1
        # 评价类别
        xspj_tables = pj_dx.find_all(attrs={'class': 'table table-bordered table-xspj'})
        for j, xspj_table in enumerate(xspj_tables):
            data['modelList[%s].xspjList[%s].pjzbxm_id' % (i, j)] = xspj_table['data-pjzbxm_id']
            # 评价项
            xspj_trs = xspj_table.find_all(attrs={'class': 'tr-xspj'})
            for x, xspj_tr in enumerate(xspj_trs):
                # 评价等级选项
                # 很好：A44133C16D2333CAE053C7EBFF74E4B8
                # 较好：A44133C16D2433CAE053C7EBFF74E4B8
                data["modelList[%s].xspjList[%s].childXspjList[%s].pfdjdmxmb_id" % (i, j, x)] = "A44133C16D2333CAE053C7EBFF74E4B8"
                # 每个评价项不同
                data["modelList[%s].xspjList[%s].childXspjList[%s].pjzbxm_id" % (i, j, x)] = xspj_tr['data-pjzbxm_id']
                # 所有都相同
                data["modelList[%s].xspjList[%s].childXspjList[%s].pfdjdmb_id" % (i, j, x)] = xspj_tr['data-pfdjdmb_id']
                # 每个评价对象不同
                data["modelList[%s].xspjList[%s].childXspjList[%s].zsmbmcb_id" % (i, j, x)] = xspj_tr['data-zsmbmcb_id']
    return data