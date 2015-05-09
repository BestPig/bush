<?php
/* Created by BestPig */

define('DATAPATH', './data/');

require 'storage.php';

$db = new Storage(DATAPATH.'/files.sqlite', DATAPATH);

if (isset($_GET['request'])) {
	if ($_GET['request'] == "upload") {
		if ($_GET['request'] == "upload" && !empty($_POST['tag']) && !empty($_FILES['file']['name'])) {
			$id = $db->addFile($_POST['tag'], $_FILES['file']['name'], 0);
			if ($id !== NULL) {
				$filepath = DATAPATH."/".$id.".bin";
				if (move_uploaded_file($_FILES['file']['tmp_name'], $filepath) && file_exists($filepath)) {
					header('HTTP/1.1 201 Created');
					echo json_encode(array(
						'status' => 'OK',
						'tag'    => $_POST['tag']
					));
					exit();
				}
			}
		}
		header('HTTP/1.1 400 Bad Request');
		echo json_encode(array(
			'status'  => 'KO',
			'message' => 'Upload requested, but no uploaded file found.')
		);
	}

	if ($_GET['request'] == "list") {
		$files = $db->getAllFiles();
		foreach ($files as &$file) {
			$filepath = DATAPATH."/".$file['id'].".bin";
			$file['date'] = date('c', filemtime($filepath));
		}
		echo json_encode($files);
		exit();
	}

	if ($_GET['request'] == 'get' && !empty($_GET['tag'])) {
		$file = $db->getFile($_GET['tag']);
		if (!empty($file[0]['id']) && !empty($file[0]['name'])) {
			$filepath = DATAPATH."/".$file[0]['id'].".bin";
			header("Content-Disposition: attachment; filename=" . urlencode($file[0]['name']));    
			header("Content-Type: application/force-download");
			header("Content-Type: application/octet-stream");
			header("Content-Type: application/download");
			header("Content-Description: File Transfer");             
			header("Content-Length: " . filesize($filepath));
			readfile($filepath);
		}
		else {
			header('HTTP/1.1 404 Not Found');
			echo "File not found.";
		}
		exit();
	}

	if ($_GET['request'] == 'delete' && !empty($_GET['tag'])) {
		$ret = $db->getFile($_GET['tag']);
		if (!empty($ret)) {
			$db->deleteFileTag($_GET['tag']);
			echo json_encode(array(
				'status' => 'OK'
			));
		}
		else {
			header('HTTP/1.1 404 Not Found');
			echo json_encode(array(
				'status' => 'KO',
				'message'=> 'Non-existing Tag')
			);
		}
		exit();
	}

	if ($_GET['request'] == 'reset') {
		$files = $db->getAllFiles();
		$i = 0;
		foreach ($files as $file) {
			$db->deleteFileId($file['id']);
			++$i;
		}
		echo json_encode(array(
			'status'        => 'OK',
			'files_deleted' => $i
		));
		exit();
	}
}

header('HTTP/1.1 400 Bad Request');
echo json_encode(array(
	'status'  => 'KO',
	'message' => 'Invalid request')
);
