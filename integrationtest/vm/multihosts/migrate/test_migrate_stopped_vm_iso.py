'''

New Integration test for testing stopped vm migration between hosts when attch ISO. 

@author: MengLai 
'''

import zstackwoodpecker.test_util as test_util
import zstackwoodpecker.test_lib as test_lib
import zstackwoodpecker.operations.volume_operations as vol_ops
import zstackwoodpecker.operations.resource_operations as res_ops
import zstackwoodpecker.operations.image_operations as img_ops
import zstackwoodpecker.zstack_test.zstack_test_image as test_image
import zstackwoodpecker.test_state as test_state
import apibinding.inventory as inventory
import os

vm = None
test_stub = test_lib.lib_get_test_stub()
test_obj_dict = test_state.TestStateDict()

def test():
    global vm
    vm = test_stub.create_vr_vm('migrate_stopped_vm', 'imageName_s', 'l3VlanNetwork2')
    test_obj_dict.add_vm(vm)
    ps = test_lib.lib_get_primary_storage_by_uuid(vm.get_vm().allVolumes[0].primaryStorageUuid)
    if ps.type != inventory.LOCAL_STORAGE_TYPE:
        test_util.test_skip('Skip test on non-localstorage')
 
    vm_inv = vm.get_vm()
    vm_uuid = vm_inv.uuid

    test_util.test_dsc('Add ISO Image')
    cond = res_ops.gen_query_conditions('name', '=', 'sftp') 
    bs_uuid = res_ops.query_resource(res_ops.BACKUP_STORAGE, cond)[0].uuid    

    img_option = test_util.ImageOption()
    img_option.set_name('iso')
    img_option.set_backup_storage_uuid_list([bs_uuid])
    os.system("echo fake iso for test only >  %s/apache-tomcat/webapps/zstack/static/test.iso" % (os.environ.get('zstackInstallPath')))
    img_option.set_url('http://%s:8080/zstack/static/test.iso' % (os.environ.get('node1Ip')))
    image_inv = img_ops.add_iso_template(img_option)
    image = test_image.ZstackTestImage()
    image.set_image(image_inv)
    image.set_creation_option(img_option)

    test_obj_dict.add_image(image)

    test_util.test_dsc('Attach ISO to VM')
    cond = res_ops.gen_query_conditions('name', '=', 'iso')
    iso_uuid = res_ops.query_resource(res_ops.IMAGE, cond)[0].uuid
    img_ops.attach_iso(iso_uuid, vm_uuid)

    test_util.test_dsc('Migrate VM')
    vm.check()
    target_host = test_lib.lib_find_random_host(vm.vm)
    vm.stop()
    vol_ops.migrate_volume(vm.get_vm().allVolumes[0].uuid, target_host.uuid)
    vm.check()
    vm.start()
    vm.check()

    img_ops.detach_iso(vm_uuid)
    image.delete()
    image.expunge()
    test_obj_dict.rm_image(image)
    vm.destroy()
    test_util.test_pass('Migrate Stopped VM Test Success When Attach ISO')

#Will be called only if exception happens in test().
def error_cleanup():
    test_lib.lib_error_cleanup(test_obj_dict)
