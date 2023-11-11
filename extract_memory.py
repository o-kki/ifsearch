import pytsk3
import os
import pyewf
import argparse
import glob
__author__ = 'ykj'
__email__ = 'jyki3848@gmail.com'
__version__ = '1.3'

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

def extract_file(file_entry, output_file):
    CHUNK_SIZE = 1024 * 1024  # 1MB
    file_size = file_entry.info.meta.size
    offset = 0
    with open(output_file, 'wb') as out_file:
        while offset < file_size:
            bytes_to_read = min(CHUNK_SIZE, file_size - offset)
            chunk = file_entry.read_random(offset, bytes_to_read)
            out_file.write(chunk)
            offset += bytes_to_read
    print(f"{output_file}로부터 추출 완료...")


def search_and_extract(part_id, fs_info, directory, collect_vm_list, output_path, parent_path="/"):
    for directory_entry in directory:
        if directory_entry.info.name.name.decode('utf-8') in [".", ".."]:
            continue
        if not directory_entry.info.meta:
            continue

        # 파일 이름이 일치하면 추출
        file_name = directory_entry.info.name.name.decode('utf-8')
        if file_name.endswith(tuple(collect_vm_list)):
            file_entry = directory_entry
            output_file = os.path.join(output_path, f"{part_id}_{file_name}")
            print(f"{output_file}로부터 추출 중...")
            extract_file(file_entry, output_file)
            print(f"{part_id}번째 파티션 {file_name} 추출 완료")

        # 디렉토리면 재귀적으로 탐색
        elif directory_entry.info.meta and directory_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            dir_name = directory_entry.info.name.name
            if dir_name.decode('utf-8').startswith('$'):
                continue
            sub_directory_path = os.path.join(parent_path, dir_name.decode('utf-8')).replace('\\', '/')
            try:
                sub_directory = fs_info.open_dir(path=sub_directory_path)
                ##search_and_extract(fs_info, sub_directory, file_name, output_path, sub_directory_path)
                search_and_extract(part_id, fs_info, sub_directory, collect_vm_list, output_path,
                                   sub_directory_path)
            except IOError as e:
                # 접근할 수 없는 디렉토리는 무시
                pass


def extract_collect_001(image_path, collect_m_list, collect_vm_list, output_path):
    img_info = pytsk3.Img_Info(image_path)
    try:
        volume = pytsk3.Volume_Info(img_info)
        for part in volume:  # 파티션마다 확인
            try:
                file_system = pytsk3.FS_Info(img_info, offset=part.start * 512)
            except:
                continue

            for file_list in collect_m_list:  # 파일 추출 로직
                try:
                    filnm = file_list.split('/')[-1]
                    file_entry = file_system.open(file_list)
                    out_file_path = output_path + os.sep + f"{part.addr}_{filnm}"
                    CHUNK_SIZE = 1024 * 1024  # 1MB
                    file_size = file_entry.info.meta.size
                    offset = 0
                    print(f"{out_file_path}로부터 추출중...")
                    with open(out_file_path, 'wb') as out_file:
                        while offset < file_size:
                            bytes_to_read = min(CHUNK_SIZE, file_size - offset)
                            chunk = file_entry.read_random(offset, bytes_to_read)
                            out_file.write(chunk)
                            offset += bytes_to_read
                    print(f"{part.desc} 내에서 {filnm} 추출 완료")
                except:
                    continue

    except IOError:  ## 단일 파티션일때
        fs_info = pytsk3.FS_Info(img_info)

        for file_list in collect_m_list:  # 파일 추출 로직
            try:
                filnm = file_list.split('/')[-1].encode('utf-8')
                file_entry = fs_info.open(file_list)
                output_file = output_path + os.sep + f"{1}_{filnm.decode('utf-8')}"
                if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    print(f"{output_file}로부터 추출중...")
                    CHUNK_SIZE = 1024 * 1024  # 1MB
                    file_size = file_entry.info.meta.size
                    offset = 0
                    with open(output_file, 'wb') as out_file:
                        while offset < file_size:
                            bytes_to_read = min(CHUNK_SIZE, file_size - offset)
                            chunk = file_entry.read_random(offset, bytes_to_read)
                            out_file.write(chunk)
                            offset += bytes_to_read
                    print(
                        f"{filnm.decode('utf-8')} 추출 완료")
            except:
                continue

    if args.virtual:
        print('가상머신 관련 메모리 파일을 검색합니다.')
        img_info = pytsk3.Img_Info(image_path)
        try:
            volume = pytsk3.Volume_Info(img_info)
            for part in volume:  # 파티션마다 확인
                try:
                    file_system = pytsk3.FS_Info(img_info, offset=part.start * 512)
                except IOError:
                    continue
                directory = file_system.open_dir(path="/")
                # 파일 목록에 있는 모든 파일 추출
                search_and_extract(part.addr, file_system, directory, collect_vm_list, output_path)
        except IOError:
            img_info = pytsk3.Img_Info(image_path)
            try:
                fs_info = pytsk3.FS_Info(img_info)
                directory = fs_info.open_dir(path="/")
                search_and_extract(1, fs_info, directory, collect_vm_list, output_path)
            except IOError as e:
                pass

def extract_collect_e01(e01_path, collect_m_list, collect_vm_list, output_path):
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
                            file_entry = fs_info.open(file_list)
                            output_file = output_path + os.sep + f"{part.addr}_{filnm.decode('utf-8')}"
                            if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                                print(f"{output_file}로부터 추출중...")
                                CHUNK_SIZE = 1024 * 1024  # 1MB
                                file_size = file_entry.info.meta.size
                                offset = 0
                                with open(output_file, 'wb') as out_file:
                                    while offset < file_size:
                                        bytes_to_read = min(CHUNK_SIZE, file_size - offset)
                                        chunk = file_entry.read_random(offset, bytes_to_read)
                                        out_file.write(chunk)
                                        offset += bytes_to_read
                                print(f"{part.addr}번째 파티션에서 {filnm.decode('utf-8')} 추출 완료")
                        except:
                            continue
                except Exception as e:
                    continue
    except IOError:  ## 단일 파티션일때
        fs_info = pytsk3.FS_Info(img_info)
        # 페이지 스왑 하이버네이션
        for file_list in collect_m_list:  # 파일 추출 로직
            try:
                filnm = file_list.split('/')[-1].encode('utf-8')
                file_entry = fs_info.open(file_list)
                output_file = output_path + os.sep + f"{part.addr}_{filnm.decode('utf-8')}"
                if file_entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    print(f"{output_file}로부터 추출중...")
                    CHUNK_SIZE = 1024 * 1024  # 1MB
                    file_size = file_entry.info.meta.size
                    offset = 0
                    with open(output_file, 'wb') as out_file:
                        while offset < file_size:
                            bytes_to_read = min(CHUNK_SIZE, file_size - offset)
                            chunk = file_entry.read_random(offset, bytes_to_read)
                            out_file.write(chunk)
                            offset += bytes_to_read
                    print(f"{part.addr}번째 파티션에서 {filnm.decode('utf-8')} 추출 완료")
            except:
                continue

    if args.virtual == True:
        print('가상머신 관련 메모리 파일을 검색합니다.')
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
                        directory = fs_info.open_dir(path="/")
                        search_and_extract(part.addr, fs_info, directory, collect_vm_list, output_path)
                    except Exception as e:
                        pass
                        # print(f"파티션 처리 중 오류 발생: {e}")
        except IOError:  # 단일 파티션일때
            fs_info = pytsk3.FS_Info(img_info)
            directory = fs_info.open_dir(path="/")
            search_and_extract(1, fs_info, directory, collect_vm_list, output_path)
        finally:
            ewf_handle.close()


if __name__ == "__main__":
    collect_m_list = ["/pagefile.sys", "/swapfile.sys", "/hiberfil.sys", "/Windows/MEMORY.DMP"]  # 메모리 파일 수집 대상
    collect_vm_list = ['.vmem', '.vmss', '.vmsn']  # 가상 메모리 파일 수집 대상

    parser = argparse.ArgumentParser(description='Unlive - Memory Files Collect from Image Files.')
    parser.add_argument('-f', '--imagepath', metavar='', help='Image Path', type=str, required=True)
    parser.add_argument('-s','--savepath', metavar='', help='Collect and Analysis Result Path', type=str, required=True)
    parser.add_argument('-v', '--virtual', metavar='', help='If you want to find Virtaul Machine Memory files....', type=str)

    args = parser.parse_args()

    if os.path.exists(args.savepath) == False:
        os.mkdir(args.savepath)

    if  os.path.splitext(args.imagepath)[1].upper() == '.E01':
        extract_collect_e01(args.imagepath, collect_m_list, collect_vm_list, args.savepath)
    else:
        extract_collect_001(args.imagepath, collect_m_list, collect_vm_list, args.savepath)
