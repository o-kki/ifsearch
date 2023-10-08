import pytsk3
import os
import pyewf
import argparse

__author__ = 'ykj'
__email__ = 'jyki3848@gmail.com'
__version__ = '1.2'

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()


def extract_collect_001(image_path, collect_m_list, collect_vm_list, output_path):
    img_info = pytsk3.Img_Info(image_path)
    volume = pytsk3.Volume_Info(img_info)

    for part in volume:  # 파티션마다 확인
        try:
            file_system = pytsk3.FS_Info(img_info, offset=part.start * 512)
        except:
            continue

        for file_list in collect_m_list:  # 파일 추출 로직
            try:
                filnm = file_list.split('/')[-1]
                file_entry = file_system.open(filnm)
                out_file_path = output_path + os.sep + f"{part.addr}_{filnm}"

                with open(out_file_path, 'wb') as out_file:
                    file_data = file_entry.read_random(0, file_entry.info.meta.size)
                    out_file.write(file_data)
                    print(f"{filnm} extraction in partition ({part.desc}) ")
            except:
                continue

        # 확장자를 통한 파일 추출
        directory = file_system.open_dir(path='/')
        for file_entry in directory:
            try:
                if file_entry.info.name.name.decode('utf-8').endswith(tuple(collect_vm_list)):
                    out_file_path = output_path + os.sep + f"{part.addr}_{file_entry.info.name.name.decode('utf-8')}"

                    with open(out_file_path, 'wb') as out_file:
                        file_data = file_entry.read_random(0, file_entry.info.meta.size)
                        out_file.write(file_data)
                    print(f"{file_entry.info.name.name.decode('utf-8')} extraction in partition ({part.desc}) ")
            except:
                continue


def extract_collect_e01(image_path, collect_m_list, collect_vm_list, output_path):
    ewf_handle = pyewf.handle()
    ewf_handle.open([image_path])

    img_info = EWFImgInfo(ewf_handle)
    fs_info = pytsk3.FS_Info(img_info)

    for file_list in collect_m_list:  # 파일 추출 로직
        try:
            filnm = file_list.split('/')[-1].encode('utf-8')
            directory = fs_info.open_dir(path="/")
            for directory_entry in directory:
                if directory_entry.info.name.name == filnm:  ## 변경
                    file_entry = directory_entry
                    output_file = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"
                    if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                        print(f"Extracting to {output_file}...")
                        with open(output_file, 'wb') as out_file:
                            file_data = file_entry.read_random(0, file_entry.info.meta.size)
                            out_file.write(file_data)
                        print(
                            f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
                        return
        except:
            continue
    # 확장자를 통한 파일 추출
    directory = fs_info.open_dir(path='/')
    for file_entry in directory:
        try:
            if file_entry.info.name.name.decode('utf-8').endswith(tuple(collect_vm_list)):
                out_file_path = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"

                with open(out_file_path, 'wb') as out_file:
                    file_data = file_entry.read_random(0, file_entry.info.meta.size)
                    out_file.write(file_data)
                print(f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
                return
        except:
            continue



def extract_collect_file_e01(e01_path, collect_m_list, collect_vm_list, output_path):
    e01_path = e01_path
    directory = e01_path.rsplit(".", 1)[0]  # E01 파일이 있는 디렉터리 가져오기
    all_segments = sorted(glob.glob(directory + ".E*"))  # 모든 E01 세그먼트 파일 가져오기

    ewf_handle = pyewf.handle()
    ewf_handle.open(all_segments)

    img_info = EWFImgInfo(ewf_handle)
    try:
        volume = pytsk3.Volume_Info(img_info)
        for part in volume:
            if part.flags == pytsk3.TSK_VS_PART_FLAG_ALLOC:  # 할당된 (사용 중인) 파티션만 처리
                try:
                    fs_info = pytsk3.FS_Info(img_info, offset=part.start * 512)  # 각 파티션의 파일 시스템 정보를 가져옴
                    for file_list in collect_m_list:  # 파일 추출 로직
                        try:
                            filnm = file_list.split('/')[-1].encode('utf-8')
                            directory = fs_info.open_dir(path="/")
                            for directory_entry in directory:
                                if directory_entry.info.name.name == filnm:  ## 변경
                                    file_entry = directory_entry
                                    output_file = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"
                                    if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                                        print(f"Extracting to {output_file}...")
                                        with open(output_file, 'wb') as out_file:
                                            file_data = file_entry.read_random(0, file_entry.info.meta.size)
                                            out_file.write(file_data)
                                        print(f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
                        except:
                            continue

                    directory = fs_info.open_dir(path='/')
                    for file_entry in directory:
                        try:
                            if file_entry.info.name.name.decode('utf-8').endswith(tuple(collect_vm_list)):
                                out_file_path = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"

                                with open(out_file_path, 'wb') as out_file:
                                    file_data = file_entry.read_random(0, file_entry.info.meta.size)
                                    out_file.write(file_data)
                                print(f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
                        except:
                            continue
                except Exception as e:
                    continue


    except IOError:  ## Single Partition
        print("볼륨 정보를 찾을 수 없습니다. 단일 파티션 이미지로 처리합니다.")
        fs_info = pytsk3.FS_Info(img_info)

        for file_list in collect_m_list:  # extract files
            try:
                filnm = file_list.split('/')[-1].encode('utf-8')
                directory = fs_info.open_dir(path="/")
                for directory_entry in directory:
                    if directory_entry.info.name.name == filnm:
                        file_entry = directory_entry
                        output_file = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"
                        if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                            print(f"Extracting to {output_file}...")
                            with open(output_file, 'wb') as out_file:
                                file_data = file_entry.read_random(0, file_entry.info.meta.size)
                                out_file.write(file_data)
                            print(f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
            except:
                continue

        directory = fs_info.open_dir(path='/')
        for file_entry in directory:
            try:
                if file_entry.info.name.name.decode('utf-8').endswith(tuple(collect_vm_list)):
                    out_file_path = output_path + os.sep + f"{directory_entry.info.name.par_addr}_{directory_entry.info.name.name.decode('utf-8')}"

                    with open(out_file_path, 'wb') as out_file:
                        file_data = file_entry.read_random(0, file_entry.info.meta.size)
                        out_file.write(file_data)
                    print(f"{directory_entry.info.name.name.decode('utf-8')} extraction in {directory_entry.info.name.par_addr}")
            except:
                continue


if __name__ == "__main__":
    collect_m_list = ["/pagefile.sys", "/swapfile.sys", "/hiberfil.sys"]  # 메모리 파일 수집 대상
    collect_vm_list = ['.vmem', '.vmss', '.vmsn']  # 가상 메모리 파일 수집 대상

    parser = argparse.ArgumentParser(description='Unlive - Memory Files Collect from Image Files.')
    parser.add_argument('-f', '--imagepath', metavar='', help='Image Path', type=str, required=True)
    parser.add_argument('-s','--savepath', metavar='', help='Collect and Analysis Result Path', type=str, required=True)

    args = parser.parse_args()

    if  os.path.splitext(args.imagepath)[1] == '.E01':
        extract_collect_e01(args.imagepath, collect_m_list, collect_vm_list, args.savepath)
    else:
        extract_collect_001(args.imagepath, collect_m_list, collect_vm_list, args.savepath)
