VM=sylabs/singularity-3.2-ubuntu-bionic64
version=$(shell cat VERSION)
CODEDIR=../..
LOGINCOMMAND="/bin/bash /vagrant/login_remote.sh"
BUILDCOMMAND="/bin/bash /vagrant/create_image.sh ${version}"
WRITABLECOMMAND="/bin/bash /vagrant/build_writable_image.sh ${version}"


create-sif-linux:
	sudo singularity build image-${version}.sif singularity.def

shell-writable-image-linux:
	singularity shell --bind ../..:/mnt --bind /tmp/.X11-unix:/tmp/.X11-unix --writable writable_image

create-writable-image-linux:
	sudo singularity build --sandbox writable_image image-${version}.sif

build-writable-to-sif-linux:
	sudo singularity build image-${version}.sif writable_image

push-sif-image-linux-to-esat:
	scp image-${version}.sif kkelchte@ssh.esat.kuleuven.be:/users/visics/kkelchte/code/imitation-learning-codebase/rosenvironment/singularity && \
	echo '! dont forget to copy from /users/visics to /gluster/visics'


shell-writable-mac:
	vagrant up
	vagrant ssh -- -t sudo singularity shell --writable /usr/data/writable_image
	# sudo mount -t ntfs /dev/sda2  /usr/data &&

writable_image-mac: #*.sif
	vagrant up
	vagrant ssh -- -t ${WRITABLECOMMAND}

Vagrantfile: Vagrantfile
	vagrant init ${VM} && \
	echo 'Adjust memory in Vagrantfile'

spinoff-vagrant: Vagrantfile
	vagrant up && \
	vagrant ssh -- -t ${LOGINCOMMAND}

shutdown-vagrant:
	vagrant halt

remove-vagrant:
	vagrant halt && \
	vagrant destroy && \
	rm -r .vagrant

*.sif: Vagrantfile VERSION requirements create_image.sh singularity.def spinoff-vagrant
	if [ -e cuda-* ] ; then \
		echo "Found cuda folder: $(echo cuda-*)"; \
		if [ -e cudnn-* ] ; then \
			echo "Found cudnn folder: $(echo cudnn-*)"; \
			vagrant ssh -- -t ${BUILDCOMMAND} && \
			cd $(CODEDIR) && \
			git commit -am "new image ${version}" && git push; \
		else \
			echo "ERROR: Could not found cudnn folder."; \
		fi ; \
	else \
		echo "ERROR: Could not found cuda folder."; \
	fi

push-image: spinoff-vagrant
	vagrant ssh -- -t ${BUILDCOMMAND}

# Following commands are for on linux machines without vagrant.

update-image:
	if [ -e *.sif ] ; then \
		for image in *.sif ; do \
			if [ $$image != ros-gazebo-cuda_${version}.sif ] ; then \
				echo "clean up: $$image"; \
				mv $$image /esat/opal/kkelchte/singularity_images; \
#				rm $$image; \
				singularity cache clean --name $$image; \
			fi ; \
		done ; \
	fi
	if [ ! -e ./ros-gazebo-cuda_${version}.sif ] ; then \
		singularity pull library://kkelchte/default/ros-gazebo-cuda:${version} && \
		echo "Successfully pulled singularity-image"; \
	else \
		echo "Singularity image already there"; \
	fi

test-image: *.sif test/singularity_sanity_check.py
	cd $(CODEDIR) && \
	singularity run --nv rosenvironment/singularity/*.sif \
	./rosenvironment/entrypoint.sh 'python3.8 rosenvironment/singularity/test/singularity_sanity_check.py'

singularity-shell:
	cd $(CODEDIR) && \
	echo "DO NOT FORGET TO SOURCE ENVIRONMENT:" && \
	echo "source rosenvironment/entrypoint.sh" && \
	singularity shell --nv rosenvironment/singularity/image-${version}.sif
