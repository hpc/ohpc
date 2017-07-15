#----------------------------------------------------------------------------bh-
# This RPM .spec file is part of the OpenHPC project.
#
# It may have been modified from the default version supplied by the underlying
# release package (if available) in order to apply patches, perform customized
# build/install configurations, and supply additional files to support
# desired integration conventions.
#
#----------------------------------------------------------------------------eh-

# scotch - Graph, mesh and hypergraph partitioning library(serial version)

#-ohpc-header-comp-begin----------------------------------------------

%include %{_sourcedir}/OHPC_macros
%{!?PROJ_DELIM: %global PROJ_DELIM -ohpc}

# OpenHPC convention: the default assumes the gnu compiler family;
# however, this can be overridden by specifing the compiler_family
# variable via rpmbuild or other mechanisms.

%{!?compiler_family: %global compiler_family gnu}

# Lmod dependency (note that lmod is pre-populated in the OpenHPC OBS build
# environment; if building outside, lmod remains a formal build dependency).
%if !0%{?OHPC_BUILD}
BuildRequires: lmod%{PROJ_DELIM}
%endif
# Compiler dependencies
%if %{compiler_family} == gnu
BuildRequires: gnu-compilers%{PROJ_DELIM}
Requires:      gnu-compilers%{PROJ_DELIM}
%endif
%if %{compiler_family} == intel
BuildRequires: intel-compilers-devel%{PROJ_DELIM}
Requires:      intel-compilers-devel%{PROJ_DELIM}
%if 0%{OHPC_BUILD}
BuildRequires: intel_licenses
%endif
%endif

#-ohpc-header-comp-end------------------------------------------------

%define pname scotch
%define PNAME %(echo %{pname} | tr [a-z] [A-Z])

Name:		%{pname}-%{compiler_family}%{PROJ_DELIM}
Version:	6.0.4
Release:	1
Summary:	Graph, mesh and hypergraph partitioning library
License:	CeCILL-C
Group:		%{PROJ_NAME}/serial-libs
URL:		http://www.labri.fr/perso/pelegrin/%{pname}/
Source0:	http://gforge.inria.fr/frs/download.php/file/34618/%{pname}_%{version}.tar.gz
Source1:	%{pname}-Makefile.inc.in
Source2:	%{pname}-rpmlintrc
Source3:        OHPC_macros
Source4:        OHPC_setup_compiler
Patch0:         %{pname}-%{version}-destdir.patch
BuildRoot:	%{_tmppath}/%{pname}-%{version}-%{release}-root
DocDir:         %{OHPC_PUB}/doc/contrib

BuildRequires:	flex bison
%if 0%{?suse_version} >= 1100
BuildRequires:  libbz2-devel
BuildRequires:  zlib-devel
%else
%if 0%{?sles_version} || 0%{?suse_version}
BuildRequires:  bzip2
BuildRequires:  zlib-devel
%else
BuildRequires:  bzip2-devel
BuildRequires:  zlib-devel
%endif
%endif

%define debug_package %{nil}
%define install_path %{OHPC_LIBS}/%{compiler_family}/%{pname}/%version

%description
Scotch is a software package for graph and mesh/hypergraph partitioning and
sparse matrix ordering.

%prep
%setup -c -q -n %{pname}_%{version}
pushd %{pname}_%{version}
%patch0 -p1
sed s/@RPMFLAGS@/'%{optflags} -fPIC'/ < %{SOURCE1} > src/Makefile.inc
popd

%build
. /etc/profile.d/lmod.sh

# OpenHPC compiler/mpi designation
export OHPC_COMPILER_FAMILY=%{compiler_family}
. %{_sourcedir}/OHPC_setup_compiler

%define dosingle() \
make %{?_smp_mflags}; \
${CC} -shared -Wl,-soname=libscotcherr.so.0 -o ../lib/libscotcherr.so.0.0	libscotch/library_error.o; \
${CC} -shared -Wl,-soname=libscotcherrexit.so.0 -o ../lib/libscotcherrexit.so.0.0	libscotch/library_error_exit.o; \
rm -f libscotch/library_error*.o; \
${CC} -shared -Wl,-soname=libscotch.so.0 -o ../lib/libscotch.so.0.0 libscotch/*.o ../lib/libscotcherr.so.0.0 -lpthread -lgfortran -lz -lbz2 -lrt; \
${CC} -shared -Wl,-soname=libscotchmetis.so.0 -o ../lib/libscotchmetis.so.0.0 libscotchmetis/*.o ../lib/libscotch.so.0.0 ../lib/libscotcherr.so.0.0 

pushd %{pname}_%{version}/src/
%dosingle
popd


%install
rm -rf %{buildroot}

%define doinst() \
pushd src/; \
make %{?_smp_mflags} install %*; \
popd \
pushd lib; \
for static_libs in *.a; do \
	libs=`basename $static_libs .a`; \
	ln -s $libs.so.0.0 $libs.so; \
	ln -s $libs.so.0.0 $libs.so.0; \
        rm -f $libdir/$static_libs; \
        cp -dp $libs.so* $libdir/; \
done; \
popd


pushd %{pname}_%{version}/
export libdir=%{buildroot}%{install_path}/lib
%doinst prefix=%{buildroot}%{install_path} libdir=%{buildroot}%{install_path}/lib

pushd %{buildroot}%{install_path}/bin
for prog in *; do
	mv $prog scotch_$prog
done
popd

pushd %{buildroot}%{install_path}/share/man/man1
rm -f d*
for prog in *; do
	mv $prog scotch_$prog
done
popd

# Convert the license files to utf8
pushd doc
iconv -f iso8859-1 -t utf-8 < CeCILL-C_V1-en.txt > CeCILL-C_V1-en.txt.conv
iconv -f iso8859-1 -t utf-8 < CeCILL-C_V1-fr.txt > CeCILL-C_V1-fr.txt.conv
mv -f CeCILL-C_V1-en.txt.conv CeCILL-C_V1-en.txt
mv -f CeCILL-C_V1-fr.txt.conv CeCILL-C_V1-fr.txt
popd

popd

# OpenHPC module file
%{__mkdir} -p %{buildroot}%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}
%{__cat} << EOF > %{buildroot}/%{OHPC_MODULEDEPS}/%{compiler_family}/%{pname}/%{version}
#%Module1.0#####################################################################

proc ModulesHelp { } {

puts stderr " "
puts stderr "This module loads the %{pname} library built with the %{compiler_family} compiler"
puts stderr "toolchain."
puts stderr "\nVersion %{version}\n"

}
module-whatis "Name: %{pname} built with %{compiler_family} compiler"
module-whatis "Version: %{version}"
module-whatis "Category: runtime library"
module-whatis "Description: %{summary}"
module-whatis "URL %{url}"

set     version			    %{version}

prepend-path    PATH                %{install_path}/bin
prepend-path    MANPATH             %{install_path}/share/man
prepend-path    INCLUDE             %{install_path}/include
prepend-path	LD_LIBRARY_PATH	    %{install_path}/lib

setenv          %{PNAME}_DIR        %{install_path}
setenv          %{PNAME}_LIB        %{install_path}/lib
setenv          %{PNAME}_INC        %{install_path}/include

EOF

%clean
rm -rf ${RPM_BUILD_ROOT}

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%files
%defattr(-,root,root)
%doc %{pname}_%{version}/README.txt %{pname}_%{version}/doc/*
%{OHPC_PUB}

%changelog

